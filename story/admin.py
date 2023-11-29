from django.contrib import admin
from story.models import Story, Content, Comment
from django.db.models import Count

class HateCountFilter(admin.SimpleListFilter):
    title = '싫어요 개수'
    parameter_name = 'hate_count'

    def lookups(self, request, model_admin):
        return (
            ('5_or_more', '5개 이상'),
        )

    def queryset(self, request, queryset):
        if self.value() == '5_or_more':
            return queryset.filter(hate_count__gte=5)


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    
    list_display = ('id', 'title', 'author', 'hate_count')
    list_per_page = 20
    list_filter = (HateCountFilter,)

@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    
    def divided_paragraph(self, obj):
        return obj.paragraph[:80]
    
    list_display = ('id', 'story', 'divided_paragraph')
    list_per_page = 20

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    
    list_display = ('id', 'content', 'author', 'story')
    list_per_page = 20