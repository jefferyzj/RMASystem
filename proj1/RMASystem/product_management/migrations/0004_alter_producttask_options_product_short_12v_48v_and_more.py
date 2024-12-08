# Generated by Django 5.1.3 on 2024-11-27 00:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product_management', '0003_remove_task_note_remove_task_result_producttask_note_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='producttask',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='product',
            name='short_12V_48V',
            field=models.CharField(choices=[('P', 'Pass'), ('F12', 'Fail on 12V'), ('F48', 'Fail on 48V')], default='P', help_text='Indicates if the product has a 12V or 48V short', max_length=10),
        ),
        migrations.AddField(
            model_name='producttask',
            name='order',
            field=models.PositiveIntegerField(db_index=True, default=0, editable=False),
        ),
        migrations.AlterField(
            model_name='product',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='product_management.location'),
        ),
        migrations.AddConstraint(
            model_name='statustask',
            constraint=models.UniqueConstraint(fields=('status', 'task'), name='unique_status_task'),
        ),
    ]
