from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UtilisateurManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("L'email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('role', 'ADMIN')
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)


class Utilisateur(AbstractUser):
    ROLES = [
        ('ADMIN',       'Administrateur'),
        ('COMPTABLE',   'Comptable'),
        ('MAGASINIER',  'Magasinier'),
        ('LABORANTIN',  'Laborantin'),
        ('MEUNIER',     'Meunier'),
        ('CLIENT',      'Client'),
    ]

    username   = None
    email      = models.EmailField(unique=True)
    nom        = models.CharField(max_length=100)
    prenom     = models.CharField(max_length=100)
    telephone  = models.CharField(max_length=20, blank=True)
    role       = models.CharField(max_length=20, choices=ROLES)
    actif      = models.BooleanField(default=True)
    profil_client = models.OneToOneField(
        'clients.Client', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='compte_utilisateur',
        help_text="Fiche client liée (rôle Client uniquement)",
    )

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom', 'role']

    objects = UtilisateurManager()

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.get_role_display()})"

    def get_full_name(self):
        return f"{self.prenom} {self.nom}".strip()

    @property
    def est_admin(self):       return self.role == 'ADMIN'
    @property
    def est_comptable(self):   return self.role == 'COMPTABLE'
    @property
    def est_magasinier(self):  return self.role == 'MAGASINIER'
    @property
    def est_laborantin(self):  return self.role == 'LABORANTIN'
    @property
    def est_meunier(self):     return self.role == 'MEUNIER'
    @property
    def est_client(self):      return self.role == 'CLIENT'
