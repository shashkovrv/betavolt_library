import os

directories = [
    # Конфигурации
    'configs',
    
    # 5-уровневый пайплайн данных
    'data/01_raw',
    'data/02_intermediate',
    'data/03_features',
    'data/04_external',
    'data/05_database',
    
    # Исходный код расчетного ядра (модульный пакет Python)
    'src',
    'src/data',
    'src/features',
    'src/models',
    'src/physics',
    'src/database',
    'src/screening',
    'src/utils',
    
    # Интерактивное веб-приложение Streamlit
    'app',
    'app/components',
    'app/pages',
    
    # Исследовательские Jupyter-ноутбуки для команды
    'notebooks',
    'notebooks/01_physics_audit',
    'notebooks/02_ml_experiments',
    'notebooks/03_radiation_defects',
    'notebooks/04_screening_pareto',
    
    # Сериализованные обученные модели и метрики
    'models',
    
    # Отчеты, научные графики и таблицы для статей и ВКР
    'reports',
    'reports/figures',
    'reports/tables',
    
    # Вспомогательные скрипты запуска и сборки
    'scripts',
    
    # Набор автотестов (pytest)
    'tests',
    'tests/unit',
    'tests/physics',
    'tests/integration',
    
    # Документация, спецификации, статьи и ВКР
    'docs/specs',
    'docs/articles',
    'docs/thesis',
]

base_dir = r'D:\project_betavolt'

for d in directories:
    full_path = os.path.join(base_dir, d.replace('/', os.sep))
    os.makedirs(full_path, exist_ok=True)
    
    # Если это пакет Python (src или tests) — создаем __init__.py
    if d.startswith('src') or d.startswith('tests'):
        init_file = os.path.join(full_path, '__init__.py')
        if not os.path.exists(init_file):
            pkg_name = d.replace('/', '.')
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(f'"""Package initialization for {pkg_name}."""\n')
    else:
        gitkeep = os.path.join(full_path, '.gitkeep')
        if not os.path.exists(gitkeep):
            with open(gitkeep, 'w', encoding='utf-8') as f:
                pass

print("Successfully created project directory tree and initialized Python packages!")
