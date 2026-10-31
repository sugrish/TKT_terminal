from django.db import migrations


def rename_signup_table(apps, schema_editor, old_table, new_table):
    table_names = set(schema_editor.connection.introspection.table_names())
    old_exists = old_table in table_names
    new_exists = new_table in table_names

    if old_exists and new_exists:
        raise RuntimeError(
            f'Cannot rename {old_table} to {new_table}: both tables exist.'
        )
    if not old_exists and not new_exists:
        raise RuntimeError(
            f'Cannot rename {old_table} to {new_table}: neither table exists.'
        )
    if old_exists:
        model = apps.get_model('body', 'Body_signup')
        schema_editor.alter_db_table(model, old_table, new_table)


def rename_signup_table_backwards(apps, schema_editor):
    rename_signup_table(
        apps,
        schema_editor,
        'employee_info',
        'body_body_signup',
    )


def rename_signup_table_forwards(apps, schema_editor):
    rename_signup_table(
        apps,
        schema_editor,
        'body_body_signup',
        'employee_info',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('body', '0008_body_signup_phone_number'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    rename_signup_table_forwards,
                    rename_signup_table_backwards,
                ),
            ],
            state_operations=[
                migrations.AlterModelTable(
                    name='body_signup',
                    table='employee_info',
                ),
            ],
        ),
    ]
