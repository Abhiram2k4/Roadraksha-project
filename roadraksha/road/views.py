from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import AuthorityProfile, AdminUser, Report
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.db.models import Q,Case, When, Value, IntegerField
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

# Create your views here.
def indexpage(request):
    return render(request,'landing.html')
def about(request):
    return render(request,'about.html')

#AUTHORITY LOGIN AND REG SECTION:
#@login_required(login_url='authlogin')
def authlogin(request):


    if request.method == "POST":
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # ✅ Empty check
        if not username_or_email or not password:
            messages.error(request, "All fields are required.")
            return redirect('authlogin')

        # ✅ Allow login using username OR email
        try:
            user_obj = User.objects.get(
                Q(username=username_or_email) | Q(email=username_or_email)
            )
            username = user_obj.username
        except User.DoesNotExist:
            messages.error(request, "Invalid username/email or password.")
            return redirect('authlogin')

        # ✅ Authenticate password
        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username/email or password.")
            return redirect('authlogin')

        # ✅ Check authority profile
        try:
            profile = AuthorityProfile.objects.get(user=user)
        except AuthorityProfile.DoesNotExist:
            messages.error(request, "Not an authority account.")
            return redirect('authlogin')

        # ✅ Check verification flag
        if not profile.is_verified:
            messages.warning(
                request,
                "Your registration request is pending. Wait for admins to verify."
            )
            return redirect('authlogin')

        # ✅ Login user
        login(request, user)

        # ✅ Redirect based on authority type
        return redirect('authority_panel', report_type=profile.authority_type)


    return render(request, 'auth_login.html')

#@login_required(login_url='authlogin')
def authreg(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        authority_type = request.POST.get('authority_type', '').strip()

        # ✅ 1. Check for empty fields
        if not username or not email or not password or not authority_type:
            messages.error(request, "!! ALL FIELDS ARE REQUIRED !!.")
            return redirect('authreg')

        # ✅ 2. Check username uniqueness
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('authreg')

        # ✅ 3. Check email uniqueness
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('authreg')

        # ✅ 4. Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # ✅ 5. Create authority profile (flag = False)
        AuthorityProfile.objects.create(
            user=user,
            authority_type=authority_type,
            is_verified=False
        )

        messages.success(
            request,
            "Registration successful. Awaiting admin verification."
        )
        return redirect('authlogin')

    return render(request, "authreg.html")

# ADMIN LOGIN AND PANEL SECTION:

def adminlogin(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # ✅ Required fields check
        if not username or not password:
            messages.error(request, "All fields are required.")
            return redirect('adminlogin')

        # ✅ Check credentials
        try:
            admin_user = AdminUser.objects.get(
                username=username,
                password=password
            )
        except AdminUser.DoesNotExist:
            messages.error(request, "Invalid admin credentials.")
            return redirect('adminlogin')

        

        return redirect('adminpanel')

    return render(request, 'adminlogin.html')
 

def adminpanel_valid(request):   #For authority registration validating page
    # 🔹 Handle ACCEPT / REJECT
    if request.method == "POST":
        profile_id = request.POST.get("profile_id")
        action = request.POST.get("action")

        profile = get_object_or_404(AuthorityProfile, id=profile_id)

        if action == "accept":
            profile.is_verified = True
            profile.save()

        elif action == "reject":
            profile.user.delete()  # deletes profile also (CASCADE)

        return redirect("adminpanel_valid")

    # 🔹 Counts
    total_requests = AuthorityProfile.objects.filter(is_verified=False).count()
    total_authorities = AuthorityProfile.objects.filter(is_verified=True).count()

    # 🔹 Pending users
    pending_profiles = AuthorityProfile.objects.filter(is_verified=False).select_related("user")

    context = {
        "total_requests": total_requests,
        "total_authorities": total_authorities,
        "pending_profiles": pending_profiles,
    }

    return render(request, "adminpanel_valid.html", context) 

def adminpanel(request):
    reports = (
        Report.objects
        .annotate(
            sort_order=Case(
                When(admin_verified=False, then=Value(0)),
                When(admin_verified=True, then=Value(1)),
                output_field=IntegerField()
            )
        )
        .order_by('sort_order', '-reported_at')
    )

    context = {
        'reports': reports,
        'total_reports': Report.objects.count(),
        'open_reports': Report.objects.filter(status=False).count(),
        'closed_reports': Report.objects.filter(status=True).count(),
    }

    return render(request,'adminpanel.html',context) 






#AUTHORITY
def authority_panel(request, report_type):
    report_type = report_type.upper()

    if report_type not in ['ROAD', 'WATER']:
        return redirect('index')

    reports = Report.objects.filter(report_type=report_type)

    total_reports = reports.count()
    open_reports = reports.filter(status=False).count()

    reports = reports.order_by('status', '-reported_at')

    context = {
        'panel_type': report_type,
        'total_reports': total_reports,
        'open_reports': open_reports,
        'reports': reports,
    }

    return render(request, 'authority_panel.html', context)



@require_POST
def resolve_report(request, report_id):
    report = get_object_or_404(Report, report_id=report_id)
    report.status = True
    report.save()
    return redirect(request.META.get('HTTP_REFERER', 'authority_panel'))

@require_POST
def admin_verified_report(request, report_id):
    report = get_object_or_404(Report, report_id=report_id)
    report.admin_verified = True
    report.save()
    return redirect(request.META.get('HTTP_REFERER', 'adminpanel'))
