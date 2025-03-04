from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from apps.accounts.models import CustomUser  # Update to import CustomUser
import uuid

def generate_po_number():
    return f"PO-{uuid.uuid4().hex[:8].upper()}"

def generate_receipt_number():
    return f"GRN-{uuid.uuid4().hex[:8].upper()}"

def generate_adjustment_number():
    return f"ADJ-{uuid.uuid4().hex[:8].upper()}"

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    tax_number = models.CharField(max_length=50, blank=True)
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    credit_period = models.PositiveIntegerField(help_text="Credit period in days")
    is_active = models.BooleanField(default=True)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

class MaterialCategory(models.Model):
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
        verbose_name_plural = "Material Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        if self.parent == self:
            raise ValidationError("Category cannot be its own parent")

class RawMaterial(models.Model):
    UNIT_CHOICES = [
        ('KG', 'Kilograms'),
        ('TON', 'Tons'),
        ('M3', 'Cubic Meters'),
        ('L', 'Liters'),
        ('PCS', 'Pieces')
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        MaterialCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='materials'
    )
    description = models.TextField()
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    current_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    minimum_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    reorder_point = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    maximum_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    default_supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        related_name='materials'
    )
    last_purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    cost_per_unit = models.DecimalField(  # New field for cost per unit
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    shelf_life = models.PositiveIntegerField(
        help_text="Shelf life in days",
        null=True,
        blank=True
    )
    storage_location = models.CharField(max_length=100)
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

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('ORDERED', 'Ordered'),
        ('PARTIALLY_RECEIVED', 'Partially Received'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled')
    ]

    TAX_TYPE_CHOICES = [
        ('A', 'Type A'),
        ('B', 'Type B'),
        ('C', 'Type C'),
    ]

    po_number = models.CharField(
        max_length=20,
        unique=True,
        default=generate_po_number
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='purchase_orders'
    )
    order_date = models.DateField()
    expected_delivery_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    tax_type = models.CharField(max_length=1, choices=TAX_TYPE_CHOICES)
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    shipping_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_purchase_orders'
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_purchase_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.po_number

    def calculate_total(self):
        items_total = sum(item.get_total_price() for item in self.items.all())
        self.tax_amount = sum(item.get_tax_amount() for item in self.items.all())  # Calculate total tax from items
        self.total_amount = items_total + self.tax_amount + self.shipping_amount - self.discount_amount
        self.save()

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    material = models.ForeignKey(
        RawMaterial,
        on_delete=models.PROTECT,
        related_name='purchase_order_items'
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    tax_type = models.CharField(
        max_length=20,
        choices=[
            ('VAT', 'Value Added Tax (VAT)'),
            ('WHT', 'Withholding Tax (WHT)'),
            ('Excise', 'Excise Duty'),
            ('Income Tax', 'Income Tax'),
            ('Corporate Tax', 'Corporate Tax'),
            ('Sales Tax', 'Sales Tax'),
        ],
        default='VAT'
    )
    received_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['purchase_order', 'material']

    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.material.name}"

    def get_total_price(self):
        total = self.quantity * self.unit_price
        discount = total * (self.discount_percentage / 100)
        return total - discount

    def get_tax_amount(self):
        # Calculate tax amount based on the total price before tax
        total_price = self.get_total_price()
        return total_price * (self.tax_rate / 100)

class StockReceipt(models.Model):
    receipt_number = models.CharField(
        max_length=20,
        unique=True,
        default=generate_receipt_number
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name='receipts'
    )
    receipt_date = models.DateField()
    received_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-receipt_date']

    def __str__(self):
        return self.receipt_number

class StockReceiptItem(models.Model):
    stock_receipt = models.ForeignKey(
        StockReceipt,
        on_delete=models.CASCADE,
        related_name='items'
    )
    purchase_order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.PROTECT,
        related_name='receipt_items'
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    batch_number = models.CharField(max_length=50)
    manufacturing_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    quality_check_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PASSED', 'Passed'),
            ('FAILED', 'Failed')
        ],
        default='PENDING'
    )
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.stock_receipt.receipt_number} - {self.purchase_order_item.material.name}"

class StockAdjustment(models.Model):
    ADJUSTMENT_TYPE_CHOICES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out')
    ]

    adjustment_number = models.CharField(
        max_length=20,
        unique=True,
        default=generate_adjustment_number
    )
    material = models.ForeignKey(
        RawMaterial,
        on_delete=models.PROTECT,
        related_name='stock_adjustments'
    )
    adjustment_type = models.CharField(max_length=3, choices=ADJUSTMENT_TYPE_CHOICES)
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    reason = models.TextField()
    adjusted_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_adjustments'
    )
    adjustment_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-adjustment_date']

    def __str__(self):
        return self.adjustment_number

class StockMovement(models.Model):
    MOVEMENT_TYPE_CHOICES = [
        ('PURCHASE', 'Purchase'),
        ('PRODUCTION', 'Production Usage'),
        ('ADJUSTMENT', 'Adjustment'),
        ('RETURN', 'Return')
    ]

    material = models.ForeignKey(
        RawMaterial,
        on_delete=models.PROTECT,
        related_name='stock_movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    reference_number = models.CharField(max_length=50)
    movement_date = models.DateTimeField()
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-movement_date']

    def __str__(self):
        return f"{self.material.name} - {self.movement_type} - {self.movement_date}"