import os
import zipfile
import time
from datetime import datetime, timedelta
import logging
import shutil

# Настройка логирования
logging.basicConfig(
    filename=r'C:\Users\pavlo\AppData\Roaming\TimeTracker\backup_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

SOURCE_FILES = [
    r'C:\Users\pavlo\AppData\Roaming\TimeTracker\usage.json',
    r'C:\Users\pavlo\AppData\Roaming\TimeTracker\logs.json'
]
BACKUP_DIR = r'C:\Users\pavlo\AppData\Roaming\TimeTracker\backup'

# Время хранения архивов (в днях)
RETENTION_DAYS = 180

def create_backup():
    try:
        # Создаем папку backup, если она не существует
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Формируем имя архива с текущей датой
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_name = os.path.join(BACKUP_DIR, f'backup_{timestamp}.zip')
        
        # Создаем ZIP-архив
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in SOURCE_FILES:
                if os.path.exists(file):
                    zipf.write(file, os.path.basename(file))
                    logging.info(f'Файл {file} добавлен в архив {zip_name}')
                else:
                    logging.warning(f'Файл {file} не найден')
        
        logging.info(f'Архив {zip_name} успешно создан')
    except Exception as e:
        logging.error(f'Ошибка при создании архива: {str(e)}')

def delete_old_backups():
    try:
        now = datetime.now()
        cutoff = now - timedelta(days=RETENTION_DAYS)
        
        for filename in os.listdir(BACKUP_DIR):
            file_path = os.path.join(BACKUP_DIR, filename)
            if os.path.isfile(file_path):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_mtime < cutoff:
                    os.remove(file_path)
                    logging.info(f'Удален старый архив: {file_path}')
    except Exception as e:
        logging.error(f'Ошибка при удалении старых архивов: {str(e)}')

def main():
    while True:
        now = datetime.now()
        # Проверяем, сегодня ли 17-е число
        if now.day == 17:
            logging.info('Запуск процесса архивации')
            create_backup()
            delete_old_backups()
            # Ждем до следующего дня, чтобы не повторять в тот же день
            time.sleep(24 * 60 * 60)
        else:
            # Проверяем каждый час
            time.sleep(60 * 60)

if __name__ == '__main__':
    main()