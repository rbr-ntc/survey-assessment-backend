"""
Authentication router with all auth endpoints.
Includes registration, login, email verification, password reset with 6-digit codes.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.auth.schemas import (MessageResponse, PasswordResetConfirm,
                              PasswordResetRequest, RefreshTokenRequest,
                              ResendVerificationCodeRequest, TokenResponse,
                              UserLogin, UserRegister, UserResponse,
                              VerificationCodeRequest)
from app.auth.utils import (create_access_token, create_refresh_token,
                            generate_verification_code,
                            get_verification_code_expiry, hash_password,
                            hash_refresh_token, verify_password, verify_token)
from app.db_postgres import get_db
from app.email_service import email_service
from app.models_postgres import AuthRefreshToken, User, VerificationCode

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# OAuth2 scheme for token extraction (fallback for Authorization header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# Dependency to extract token from header or cookie
async def get_token(
    request: Request,
    authorization: Optional[str] = None,
    access_token: Optional[str] = Cookie(None),
) -> Optional[str]:
    """
    Extract token from Authorization header or access_token cookie.
    Priority: Authorization header > Cookie
    """
    # Try Authorization header first
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ")[1]
    
    # Fallback to cookie
    if access_token:
        return access_token
    
    # Try to get from request headers directly
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    
    return None


# Dependency for getting current user
async def get_current_user(
    token: Optional[str] = Depends(get_token),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    Supports both Authorization header and httpOnly cookie.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    payload = verify_token(token, token_type="access")
    if not payload:
        raise credentials_exception
    
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception
    
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise credentials_exception
    
    return user


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Register new user.
    Creates user account and sends 6-digit verification code to email.
    """
    try:
        logger.info(f"Registration attempt for email: {user_data.email}")
        
        # Verify database connection
        from app.config import settings
        from app.db_postgres import get_engine
        try:
            engine = get_engine()
            logger.debug("Database engine initialized successfully")
        except ValueError as e:
            logger.error(f"Database configuration error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка конфигурации базы данных. Обратитесь в поддержку.",
            )
        
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == user_data.email, User.deleted_at.is_(None)))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.warning(f"Registration failed: user with email {user_data.email} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует",
            )

        # Create new user
        logger.debug("Hashing password...")
        hashed_password = hash_password(user_data.password)
        
        logger.debug("Creating user object...")
        new_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            name=user_data.name,
            role="student",
            email_verified=False,
        )
        
        logger.debug("Adding user to session...")
        db.add(new_user)
        await db.flush()  # Get user ID
        logger.debug(f"User created with ID: {new_user.id}")
        
        # Generate verification code
        logger.debug("Generating verification code...")
        code = generate_verification_code()
        verification_code = VerificationCode(
            user_id=new_user.id,
            code=code,
            code_type="email_verification",
            expires_at=get_verification_code_expiry(),
        )
        
        logger.debug("Adding verification code to session...")
        db.add(verification_code)
        
        logger.debug("Committing transaction...")
        await db.commit()
        logger.info(f"User {user_data.email} registered successfully")
        
        # Send verification email (non-blocking - don't fail registration if email fails)
        try:
            logger.debug("Sending verification email...")
            await email_service.send_email(
                to_email=user_data.email,
                subject="Подтверждение email - LearnHub LMS",
                html_body=email_service.render_verification_code_template(code, user_data.name),
            )
            logger.info(f"Verification email sent to {user_data.email}")
        except Exception as e:
            # Log error but don't fail registration
            logger.error(f"Failed to send verification email to {user_data.email}: {e}", exc_info=True)
            # Registration still succeeds, user can request code resend
        
        return MessageResponse(
            message="Регистрация успешна. Проверьте email для подтверждения адреса."
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like user already exists)
        raise
    except Exception as e:
        logger.error(f"Registration failed for {user_data.email}: {e}", exc_info=True)
        # Don't expose internal error details to user, but log them
        error_detail = "Ошибка при регистрации. Попробуйте позже или обратитесь в поддержку."
        error_str = str(e).lower()
        if "duplicate key" in error_str or "already exists" in error_str:
            error_detail = "Пользователь с таким email уже существует"
        elif "connection" in error_str or "database" in error_str or "postgres" in error_str:
            error_detail = "Ошибка подключения к базе данных"
        elif "timeout" in error_str:
            error_detail = "Превышено время ожидания. Попробуйте позже."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
        )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    request: VerificationCodeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Verify email with 6-digit code.
    """
    # Find verification code
    result = await db.execute(
        select(VerificationCode)
        .where(
            VerificationCode.code == request.code,
            VerificationCode.code_type == "email_verification",
            VerificationCode.used_at.is_(None),
            VerificationCode.deleted_at.is_(None),
            VerificationCode.expires_at > datetime.now(timezone.utc),
        )
    )
    verification = result.scalar_one_or_none()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или истекший код подтверждения",
        )
    
    # Mark code as used
    verification.used_at = datetime.now(timezone.utc)
    
    # Verify user email
    user_result = await db.execute(select(User).where(User.id == verification.user_id))
    user = user_result.scalar_one()
    user.email_verified = True
    
    await db.commit()
    
    # Send welcome email (non-blocking)
    try:
        await email_service.send_email(
            to_email=user.email,
            subject="Добро пожаловать в LearnHub LMS!",
            html_body=email_service.render_welcome_template(user.name),
        )
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {e}")
    
    return MessageResponse(message="Email успешно подтвержден")


@router.post("/resend-verification-code", response_model=MessageResponse)
async def resend_verification_code(
    request: ResendVerificationCodeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Resend verification code to user's email.
    Useful if user didn't receive the code or it expired.
    """
    # Find user
    result = await db.execute(
        select(User).where(User.email == request.email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if user exists or not (security best practice)
        return MessageResponse(
            message="Если email зарегистрирован, код подтверждения отправлен на почту."
        )
    
    # If email already verified, no need to send code
    if user.email_verified:
        return MessageResponse(
            message="Email уже подтвержден. Вы можете войти в систему."
        )
    
    # Generate new verification code
    code = generate_verification_code()
    verification_code = VerificationCode(
        user_id=user.id,
        code=code,
        code_type="email_verification",
        expires_at=get_verification_code_expiry(),
    )
    
    db.add(verification_code)
    await db.commit()
    
    # Send verification email (non-blocking)
    try:
        await email_service.send_email(
            to_email=user.email,
            subject="Код подтверждения email - LearnHub LMS",
            html_body=email_service.render_verification_code_template(code, user.name),
        )
        logger.info(f"Verification code resent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}", exc_info=True)
        # Still return success message for security (don't reveal email issues)
    
    return MessageResponse(
        message="Если email зарегистрирован, код подтверждения отправлен на почту."
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Login user and return access + refresh tokens.
    """
    # Find user
    result = await db.execute(
        select(User).where(User.email == user_data.email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    
    # Verify password
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    
    # Check if email is verified
    # Note: For development, we allow login without verification, but in production
    # you might want to enforce this. Comment out the check below to allow unverified logins.
    if not user.email_verified:
        # Instead of blocking, return a message suggesting to verify email
        # But still allow login for better UX (user can verify later)
        logger.warning(f"User {user.email} logged in without verified email")
        # Uncomment below to enforce email verification:
        # raise HTTPException(
        #     status_code=status.HTTP_403_FORBIDDEN,
        #     detail="Email не подтвержден. Проверьте почту для кода подтверждения или запросите новый код.",
        # )
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Store refresh token hash in database
    refresh_token_hash = hash_refresh_token(refresh_token)
    refresh_token_record = AuthRefreshToken(
        user_id=user.id,
        token_hash=refresh_token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    
    db.add(refresh_token_record)
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Refresh access token using refresh token.
    """
    # Verify refresh token
    payload = verify_token(request.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или истекший refresh token",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
        )
    
    # Check if refresh token exists in database and is not revoked
    refresh_token_hash = hash_refresh_token(request.refresh_token)
    result = await db.execute(
        select(AuthRefreshToken)
        .where(
            AuthRefreshToken.token_hash == refresh_token_hash,
            AuthRefreshToken.revoked_at.is_(None),
            AuthRefreshToken.deleted_at.is_(None),
            AuthRefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    token_record = result.scalar_one_or_none()
    
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не найден или отозван",
        )
    
    # Get user
    user_result = await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    
    # Create new tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Revoke old refresh token
    token_record.revoked_at = datetime.now(timezone.utc)
    
    # Store new refresh token
    new_refresh_token_hash = hash_refresh_token(new_refresh_token)
    new_token_record = AuthRefreshToken(
        user_id=user.id,
        token_hash=new_refresh_token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    
    db.add(new_token_record)
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get current authenticated user.
    """
    return current_user


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: PasswordResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Request password reset. Sends 6-digit code to email.
    """
    # Find user
    result = await db.execute(
        select(User).where(User.email == request.email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if user exists
        return MessageResponse(
            message="Если пользователь с таким email существует, код восстановления отправлен на почту."
        )
    
    # Generate verification code
    code = generate_verification_code()
    verification_code = VerificationCode(
        user_id=user.id,
        code=code,
        code_type="password_reset",
        expires_at=get_verification_code_expiry(),
    )
    
    db.add(verification_code)
    await db.commit()
    
    # Send password reset email (non-blocking)
    try:
        await email_service.send_email(
            to_email=user.email,
            subject="Восстановление пароля - LearnHub LMS",
            html_body=email_service.render_password_reset_template(code, user.name),
        )
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")
    
    return MessageResponse(
        message="Если пользователь с таким email существует, код восстановления отправлен на почту."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: PasswordResetConfirm,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Reset password using 6-digit verification code.
    """
    # Find verification code
    result = await db.execute(
        select(VerificationCode)
        .where(
            VerificationCode.code == request.code,
            VerificationCode.code_type == "password_reset",
            VerificationCode.used_at.is_(None),
            VerificationCode.deleted_at.is_(None),
            VerificationCode.expires_at > datetime.now(timezone.utc),
        )
    )
    verification = result.scalar_one_or_none()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или истекший код подтверждения",
        )
    
    # Get user
    user_result = await db.execute(
        select(User).where(
            User.id == verification.user_id,
            User.email == request.email,
            User.deleted_at.is_(None),
        )
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не найден",
        )
    
    # Mark code as used
    verification.used_at = datetime.now(timezone.utc)
    
    # Update password
    user.password_hash = hash_password(request.new_password)
    
    # Revoke all refresh tokens for security
    from sqlalchemy import update
    await db.execute(
        update(AuthRefreshToken)
        .where(
            AuthRefreshToken.user_id == user.id,
            AuthRefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(timezone.utc))
    )
    
    await db.commit()
    
    return MessageResponse(message="Пароль успешно изменен")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Logout user by revoking refresh token.
    """
    refresh_token_hash = hash_refresh_token(request.refresh_token)
    
    result = await db.execute(
        select(AuthRefreshToken)
        .where(
            AuthRefreshToken.token_hash == refresh_token_hash,
            AuthRefreshToken.revoked_at.is_(None),
        )
    )
    token_record = result.scalar_one_or_none()
    
    if token_record:
        token_record.revoked_at = datetime.now(timezone.utc)
        await db.commit()
    
    return MessageResponse(message="Выход выполнен успешно")



