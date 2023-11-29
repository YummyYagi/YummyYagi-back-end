# Generated by Django 4.2.7 on 2023-11-29 00:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_paymentresult_ticket'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='country',
            field=models.CharField(choices=[('대한민국', '대한민국'), ('미국', '미국'), ('프랑스', '프랑스'), ('스페인', '스페인'), ('일본', '일본'), ('중국', '중국'), ('', '')], max_length=50, verbose_name='국가'),
        ),
    ]
