from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.accounts.models import Employee
from apps.inventory.models import RawMaterial
import uuid

def generate_schedule_number():
    return f"PS-{uuid.uuid4().hex[:8].upper()}"

class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Product Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    UNIT_CHOICES = [
        ('KG', 'Kilograms'),
        ('TON', 'Tons'),
        ('PCS', 'Pieces'),
        ('BOX', 'Box'),
        ('PKT', 'Packet')
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('DISCONTINUED', 'Discontinued'),
        ('DEVELOPMENT', 'In Development')
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    description = models.TextField()
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    batch_size = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    minimum_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    maximum_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    reorder_point = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    current_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    standard_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    shelf_life = models.PositiveIntegerField(
        help_text="Shelf life in days",
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        if self.minimum_stock > self.maximum_stock:
            raise ValidationError("Minimum stock cannot be greater than maximum stock")
        if self.reorder_point < self.minimum_stock:
            raise ValidationError("Reorder point must be greater than minimum stock")
        if self.reorder_point > self.maximum_stock:
            raise ValidationError("Reorder point cannot be greater than maximum stock")

class ProductFormula(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='formulas'
    )
    version = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True
    )
    approved_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_formulas'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'version']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - Version {self.version}"

class FormulaItem(models.Model):
    formula = models.ForeignKey(
        ProductFormula,
        on_delete=models.CASCADE,
        related_name='items'
    )
    material = models.ForeignKey(
        RawMaterial,
        on_delete=models.PROTECT,
        related_name='formula_items'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)]
    )
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['formula', 'material']

    def __str__(self):
        return f"{self.formula.product.name} - {self.material.name}"

class ProductMovement(models.Model):
    MOVEMENT_TYPE_CHOICES = [
        ('PRODUCTION', 'Production'),
        ('SALES', 'Sales'),
        ('RETURN', 'Return'),
        ('ADJUSTMENT', 'Adjustment')
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='stock_movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    reference_number = models.CharField(max_length=50)
    movement_date = models.DateTimeField()
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-movement_date']

    def __str__(self):
        return f"{self.product.name} - {self.movement_type} - {self.movement_date}"