from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from user.models import User


class UserCreationForm(forms.ModelForm):
    """
    사용자 생성 폼입니다.
    
    관리자 페이지에서 새로운 사용자를 생성하기 위한 양식으로 필수 필드와 
    """
    password1 = forms.CharField(label="비밀번호", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="비밀번호 확인", widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ["email", "nickname", "profile_img", "country"]

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("비밀번호가 비밀번호 확인과 일치하지 않습니다.")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """
    사용자 정보 수정 폼입니다.
    
    이 폼은 사용자 정보를 편집하는 양식으로 
    사용자(User) 모델에 정의된 모든 필드를 포함하지만
    비밀번호 필드는 해시된 비밀번호로만 표시하고 수정할 수 없도록 합니다.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ["email", "password", "nickname",
                  "is_active", "is_admin", "profile_img", "country"]


class UserAdmin(BaseUserAdmin):
    """
    사용자 관리자 설정입니다.

    사용자 정보를 생성하거나 수정할 때 사용되는 양식입니다.
    """
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ["email", "is_admin", "nickname", "profile_img", "country"]
    list_filter = ["is_admin"]
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        ("Personal info", {"fields": ["nickname", "profile_img", "country"]}),
        ("Permissions", {"fields": ["is_admin"]}),
    ]
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": ["email", "password1", "password2", "nickname", "profile_img", "country"],
            },
        ),
    ]
    search_fields = ["email"]
    ordering = ["email"]
    filter_horizontal = []


admin.site.register(User, UserAdmin)    # 관리자 페이지에 사용자(User) 모델을 등록합니다.
admin.site.unregister(Group)            # 관리자 페이지에서 기본적으로 제공되는 그룹(Group) 모델을 등록 해제합니다.
