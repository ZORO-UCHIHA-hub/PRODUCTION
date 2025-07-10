from dashboard.models import BranchProduct, Profile
from dashboard.utils.whatsapp import send_whatsapp_message

def notify_low_stock(branch_product):
    if branch_product.stock < 5:
        managers = Profile.objects.filter(branch=branch_product.branch, role='manager', phone__isnull=False)
        for manager in managers:
            message = f"⚠️ Low Stock Alert\n\nProduct: {branch_product.product.name}\nStock left: {branch_product.stock}\nBranch: {branch_product.branch.name}"
            send_whatsapp_message(manager.phone, message)
