from django.db import models
from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser, BaseUserManager

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, username, password=None, **extra_fields):
        """
        Create and save a user with the given email and password.
        """

        if not username:
            raise ValueError("The 'username' must be set")
        
        user = self.model(username=username, **extra_fields)
        user.set_password(password)  # Set and hash the password
        user.save(using=self._db)  # Ensure to save using the database that the manager is bound to
        
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(("Superuser must have is_superuser=True."))
        
        return self.create_user(username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = (
        ('organizer', 'Organizer'),
        ('normal', 'Normal'),
    )
    username = models.CharField(unique=True, max_length=50)
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    objects = CustomUserManager()

    def __str__(self):
        return self.username

    def is_organizer(self):
        return self.user_type == 'organizer'
    
    def is_normal(self):
        return self.user_type == 'normal'