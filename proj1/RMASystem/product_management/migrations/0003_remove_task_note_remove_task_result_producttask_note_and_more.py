# Generated by Django 5.1.3 on 2024-11-26 01:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product_management', '0002_productstatus_statustransition_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='note',
        ),
        migrations.RemoveField(
            model_name='task',
            name='result',
        ),
        migrations.AddField(
            model_name='producttask',
            name='note',
            field=models.TextField(blank=True, help_text='User can write down some notes on this task of this product', null=True),
        ),
        migrations.AddField(
            model_name='producttask',
            name='result',
            field=models.TextField(blank=True, default='Action Not Yet Done', help_text='Result of the task of the product', null=True),
        ),
        migrations.AlterField(
            model_name='producttask',
            name='is_completed',
            field=models.BooleanField(default=False, help_text='Indicates if the task is completed'),
        ),
        migrations.AlterField(
            model_name='producttask',
            name='is_skipped',
            field=models.BooleanField(default=False, help_text='Indicates if the task is skipped'),
        ),
        migrations.AddConstraint(
            model_name='producttask',
            constraint=models.UniqueConstraint(condition=models.Q(('is_completed', False), ('is_skipped', False)), fields=('product', 'task'), name='unique_active_product_task'),
        ),
    ]