import json
import datetime
import os

# ------------------------- КЛАСС ЦЕЛИ -------------------------
class Goal:
    """Представляет цель накопления."""
    def __init__(self, name, target, balance=0.0, category="Другое",
                 deadline=None, planned_amount=None, frequency=None):
        self.name = name
        self.target = target
        self.balance = balance
        self.category = category
        self.deadline = deadline               # datetime.date or None
        self.planned_amount = planned_amount   # сумма пополнения (float)
        self.frequency = frequency             # 'weekly' or 'monthly'
        self.status = self._compute_status()
        self.notified_percentages = set()      # для уведомлений о вехах

    def _compute_status(self):
        return "выполнена" if self.balance >= self.target else "в процессе"

    def update_balance(self, amount, is_increase=True):
        """Увеличить/уменьшить баланс с проверками."""
        if is_increase:
            new_balance = self.balance + amount
            if new_balance > self.target:
                print("❗ Ошибка: нельзя превысить итоговую сумму!")
                return False
            self.balance = new_balance
        else:
            new_balance = self.balance - amount
            if new_balance < 0:
                print("❗ Ошибка: баланс не может быть отрицательным!")
                return False
            self.balance = new_balance

        self.status = self._compute_status()
        self._check_progress_notification()
        return True

    def _check_progress_notification(self):
        """Уведомление при достижении 10%, 25%, 50%, 75%, 90%, 100%."""
        milestones = [10, 25, 50, 75, 90, 100]
        if self.target == 0:
            return
        percent = (self.balance / self.target) * 100
        for m in milestones:
            if percent >= m and m not in self.notified_percentages:
                print(f"🎉 Уведомление: цель '{self.name}' достигла {m}% прогресса!")
                self.notified_percentages.add(m)

    def progress_percent(self):
        """Процент выполнения цели."""
        if self.target == 0:
            return 100.0
        return (self.balance / self.target) * 100

    def to_dict(self):
        """Сериализация в словарь для JSON."""
        return {
            "name": self.name,
            "target": self.target,
            "balance": self.balance,
            "category": self.category,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "planned_amount": self.planned_amount,
            "frequency": self.frequency,
            "notified_percentages": list(self.notified_percentages)
        }

    @classmethod
    def from_dict(cls, data):
        """Восстановление объекта из словаря."""
        deadline = None
        if data["deadline"]:
            deadline = datetime.date.fromisoformat(data["deadline"])
        goal = cls(
            name=data["name"],
            target=data["target"],
            balance=data["balance"],
            category=data["category"],
            deadline=deadline,
            planned_amount=data["planned_amount"],
            frequency=data["frequency"]
        )
        goal.notified_percentages = set(data.get("notified_percentages", []))
        goal.status = goal._compute_status()
        return goal

# ------------------------- ОСНОВНОЕ ПРИЛОЖЕНИЕ -------------------------
class PiggyBankApp:
    """Консольное приложение «Копилка»."""
    DATA_FILE = "piggybank.json"

    def __init__(self):
        self.goals = []
        self.load_data()

    def load_data(self):
        """Загружает цели из JSON-файла."""
        if not os.path.exists(self.DATA_FILE):
            return
        try:
            with open(self.DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.goals = [Goal.from_dict(item) for item in data]
        except (json.JSONDecodeError, KeyError, TypeError):
            print("⚠️ Ошибка при загрузке файла. Будет создан новый список целей.")

    def save_data(self):
        """Сохраняет цели в JSON-файл."""
        try:
            with open(self.DATA_FILE, "w", encoding="utf-8") as f:
                json.dump([goal.to_dict() for goal in self.goals], f,
                          ensure_ascii=False, indent=4)
        except IOError:
            print("⚠️ Ошибка сохранения данных!")

    # ------------------------- БАЗОВЫЕ ОПЕРАЦИИ -------------------------
    def add_goal(self):
        """Интерактивное добавление новой цели."""
        print("\n--- Добавление новой цели ---")
        name = input("Название цели: ").strip()
        if not name:
            print("Название не может быть пустым!")
            return

        try:
            target = float(input("Итоговая сумма (руб): "))
            if target <= 0:
                print("Сумма должна быть положительной!")
                return
        except ValueError:
            print("Некорректное число!")
            return

        # Категория
        categories = ["Работа", "Здоровье", "Отдых", "Образование", "Другое"]
        print("Доступные категории:", ", ".join(categories))
        cat = input("Категория (можно ввести свою): ").strip()
        if cat not in categories:
            categories.append(cat)

        # Дедлайн (опционально)
        deadline = None
        add_deadline = input("Установить дедлайн? (д/н): ").lower()
        if add_deadline == 'д':
            date_str = input("Дата (ГГГГ-ММ-ДД): ")
            try:
                deadline = datetime.date.fromisoformat(date_str)
            except ValueError:
                print("Неверный формат, дедлайн не установлен.")

        # Плановые пополнения (для расчёта даты завершения – повышенный уровень)
        planned_amount = None
        frequency = None
        add_plan = input("Задать плановые пополнения для прогноза даты? (д/н): ").lower()
        if add_plan == 'д':
            try:
                planned_amount = float(input("Сумма пополнения: "))
                if planned_amount <= 0:
                    print("Сумма должна быть >0, пропускаем.")
                    planned_amount = None
                else:
                    freq = input("Частота (weekly/monthly): ").lower()
                    if freq in ('weekly', 'monthly'):
                        frequency = freq
                    else:
                        print("Неизвестная частота, прогноз даты недоступен.")
                        planned_amount = None
            except ValueError:
                print("Некорректная сумма.")

        # Начальный баланс (по желанию)
        initial = 0.0
        set_initial = input("Указать начальный баланс? (д/н): ").lower()
        if set_initial == 'д':
            try:
                initial = float(input("Текущая сумма: "))
                if initial < 0:
                    print("Баланс не может быть отрицательным, установлено 0.")
                    initial = 0.0
                if initial > target:
                    print("Начальный баланс не может превышать цель. Установлен 0.")
                    initial = 0.0
            except ValueError:
                print("Некорректное число, баланс = 0.")

        new_goal = Goal(name, target, initial, cat, deadline, planned_amount, frequency)
        self.goals.append(new_goal)
        self.save_data()
        print(f"✅ Цель '{name}' добавлена!")

    def list_goals(self):
        """Вывод всех целей с краткой информацией."""
        if not self.goals:
            print("📭 Список целей пуст.")
            return
        print("\n--- Список целей ---")
        for idx, g in enumerate(self.goals, 1):
            deadline_str = g.deadline.isoformat() if g.deadline else "—"
            print(f"{idx}. {g.name} | {g.category} | {g.balance:.2f}/{g.target:.2f} руб. "
                  f"({g.progress_percent():.1f}%) | Статус: {g.status} | Дедлайн: {deadline_str}")

    def choose_goal(self, prompt="Выберите номер цели"):
        """Вспомогательный метод для выбора цели по индексу."""
        if not self.goals:
            print("Нет ни одной цели.")
            return None
        self.list_goals()
        try:
            choice = int(input(f"{prompt}: ")) - 1
            if 0 <= choice < len(self.goals):
                return self.goals[choice]
            else:
                print("Неверный номер.")
                return None
        except ValueError:
            print("Введите число.")
            return None

    def update_balance(self):
        """Увеличение или уменьшение баланса выбранной цели."""
        goal = self.choose_goal("Выберите цель для изменения баланса")
        if not goal:
            return
        print(f"Текущий баланс '{goal.name}': {goal.balance:.2f} / {goal.target:.2f}")
        action = input("Действие (+ увеличение / - уменьшение): ").strip()
        try:
            amount = float(input("Сумма: "))
            if amount <= 0:
                print("Сумма должна быть положительной.")
                return
        except ValueError:
            print("Некорректная сумма.")
            return

        if action == '+':
            if goal.update_balance(amount, is_increase=True):
                self.save_data()
                print(f"✅ Баланс увеличен. Новый баланс: {goal.balance:.2f}")
        elif action == '-':
            if goal.update_balance(amount, is_increase=False):
                self.save_data()
                print(f"✅ Баланс уменьшен. Новый баланс: {goal.balance:.2f}")
        else:
            print("Неверное действие. Используйте + или -.")

    def delete_goal(self):
        """Удаление цели."""
        goal = self.choose_goal("Выберите цель для удаления")
        if not goal:
            return
        confirm = input(f"Удалить цель '{goal.name}'? (д/н): ").lower()
        if confirm == 'д':
            self.goals.remove(goal)
            self.save_data()
            print("🗑️ Цель удалена.")

    def view_progress(self):
        """Просмотр прогресса выбранной цели или всех."""
        if not self.goals:
            print("Нет целей.")
            return
        print("\n1. Прогресс по одной цели")
        print("2. Прогресс по всем целям")
        sub = input("Выбор: ").strip()
        if sub == '1':
            goal = self.choose_goal()
            if goal:
                print(f"\n📊 Цель: {goal.name}")
                print(f"   Категория: {goal.category}")
                print(f"   Накоплено: {goal.balance:.2f} / {goal.target:.2f} руб.")
                print(f"   Процент выполнения: {goal.progress_percent():.2f}%")
                print(f"   Статус: {goal.status}")
        elif sub == '2':
            for g in self.goals:
                print(f"• {g.name}: {g.balance:.2f}/{g.target:.2f} ({g.progress_percent():.1f}%)")
        else:
            print("Неверный выбор.")

    def filter_by_category(self):
        """Показать цели выбранной категории."""
        if not self.goals:
            print("Нет целей.")
            return
        cats = sorted(set(g.category for g in self.goals))
        print("Категории:", ", ".join(cats))
        cat = input("Введите категорию: ").strip()
        filtered = [g for g in self.goals if g.category.lower() == cat.lower()]
        if not filtered:
            print("Нет целей в этой категории.")
        else:
            for g in filtered:
                print(f"- {g.name}: {g.balance:.2f}/{g.target:.2f} ({g.progress_percent():.1f}%)")

    def overall_progress(self):
        """Подсчёт общего прогресса по всем целям (доп. функция)."""
        if not self.goals:
            print("Нет целей для подсчёта.")
            return
        total_balance = sum(g.balance for g in self.goals)
        total_target = sum(g.target for g in self.goals)
        if total_target == 0:
            percent = 100.0
        else:
            percent = (total_balance / total_target) * 100
        print("\n📈 Общий прогресс по всем целям:")
        print(f"   Суммарно накоплено: {total_balance:.2f} / {total_target:.2f} руб.")
        print(f"   Общий процент выполнения: {percent:.2f}%")

    # ------------------------- ПОВЫШЕННЫЙ УРОВЕНЬ -------------------------
    def set_planned_deposit(self):
        """Установить/изменить плановые пополнения для цели (для прогноза даты)."""
        goal = self.choose_goal("Выберите цель для настройки плановых пополнений")
        if not goal:
            return
        try:
            amount = float(input("Сумма планового пополнения (0 – отключить): "))
            if amount < 0:
                print("Сумма не может быть отрицательной.")
                return
            if amount == 0:
                goal.planned_amount = None
                goal.frequency = None
                print("Плановые пополнения отключены.")
                self.save_data()
                return
            freq = input("Частота (weekly/monthly): ").lower()
            if freq not in ('weekly', 'monthly'):
                print("Неверная частота. Настройка не сохранена.")
                return
            goal.planned_amount = amount
            goal.frequency = freq
            self.save_data()
            print("✅ Плановые пополнения сохранены.")
        except ValueError:
            print("Некорректная сумма.")

    def suggest_completion_date(self, goal):
        """Рассчитать ожидаемую дату завершения на основе плановых пополнений."""
        if goal.target <= goal.balance:
            return "Цель уже выполнена!"
        if not goal.planned_amount or not goal.frequency:
            return "Не заданы плановые пополнения. Используйте 'Настроить плановые пополнения'."

        remaining = goal.target - goal.balance
        # Количество пополнений до достижения цели
        periods_needed = remaining / goal.planned_amount
        if periods_needed <= 0:
            return "Уже выполнено!"

        today = datetime.date.today()
        if goal.frequency == 'weekly':
            delta_days = int(periods_needed * 7)
        else:  # monthly
            delta_days = int(periods_needed * 30)  # приблизительно
        estimated_date = today + datetime.timedelta(days=delta_days)
        return f"При регулярных пополнениях по {goal.planned_amount} руб. {goal.frequency} ожидаемая дата завершения: {estimated_date.isoformat()}"

    def check_reminders_and_suggestions(self):
        """Напоминания о дедлайнах и предложение дат завершения."""
        if not self.goals:
            print("Нет целей.")
            return
        today = datetime.date.today()
        print("\n--- Напоминания по дедлайнам ---")
        for g in self.goals:
            if g.deadline and g.status != "выполнена":
                if g.deadline < today:
                    print(f"⚠️ ПРОСРОЧЕНА цель '{g.name}'! Дедлайн был {g.deadline.isoformat()}")
                elif (g.deadline - today).days <= 7:
                    print(f"⏰ Приближается дедлайн цели '{g.name}': {g.deadline.isoformat()} (осталось {(g.deadline - today).days} дн.)")

        print("\n--- Прогноз даты завершения (на основе плановых пополнений) ---")
        for g in self.goals:
            if g.status != "выполнена":
                suggestion = self.suggest_completion_date(g)
                if "Не заданы" not in suggestion and "Уже выполнена" not in suggestion:
                    print(f"📅 {g.name}: {suggestion}")

    # ------------------------- ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ -------------------------
    def edit_goal(self):
        """Редактирование параметров цели."""
        goal = self.choose_goal("Выберите цель для редактирования")
        if not goal:
            return
        print("Оставьте поле пустым, чтобы не менять.")
        new_name = input(f"Название ({goal.name}): ").strip()
        if new_name:
            goal.name = new_name
        try:
            new_target = input(f"Новая итоговая сумма ({goal.target}): ").strip()
            if new_target:
                new_target = float(new_target)
                if new_target <= 0:
                    print("Сумма должна быть >0, оставлена старая.")
                else:
                    if new_target < goal.balance:
                        print("Цель не может быть меньше текущего баланса. Баланс будет скорректирован.")
                        goal.balance = new_target
                    goal.target = new_target
        except ValueError:
            print("Некорректное число, сумма не изменена.")
        # Категорию тоже можно поменять
        new_cat = input(f"Категория ({goal.category}): ").strip()
        if new_cat:
            goal.category = new_cat
        # Дедлайн
        new_deadline = input("Новый дедлайн (ГГГГ-ММ-ДД) или Enter пропустить: ").strip()
        if new_deadline:
            try:
                goal.deadline = datetime.date.fromisoformat(new_deadline)
            except ValueError:
                print("Неверный формат, дедлайн не изменён.")
        goal.status = goal._compute_status()
        self.save_data()
        print("✅ Цель обновлена.")

    # ------------------------- ГЛАВНОЕ МЕНЮ -------------------------
    def run(self):
        """Запуск основного цикла приложения."""
        while True:
            print("\n" + "="*50)
            print("      КОПИЛКА - Управление накоплениями")
            print("="*50)
            print("1. Добавить цель")
            print("2. Список всех целей")
            print("3. Изменить баланс цели (+/-)")
            print("4. Просмотреть прогресс")
            print("5. Удалить цель")
            print("6. Фильтр по категории")
            print("7. Общий прогресс по всем целям")
            print("8. Настроить плановые пополнения (прогноз даты)")
            print("9. Напоминания и предложение даты завершения")
            print("10. Редактировать цель")
            print("0. Выход")
            choice = input("Ваш выбор: ").strip()

            if choice == '1':
                self.add_goal()
            elif choice == '2':
                self.list_goals()
            elif choice == '3':
                self.update_balance()
            elif choice == '4':
                self.view_progress()
            elif choice == '5':
                self.delete_goal()
            elif choice == '6':
                self.filter_by_category()
            elif choice == '7':
                self.overall_progress()
            elif choice == '8':
                self.set_planned_deposit()
            elif choice == '9':
                self.check_reminders_and_suggestions()
            elif choice == '10':
                self.edit_goal()
            elif choice == '0':
                self.save_data()
                print("До свидания! Данные сохранены.")
                break
            else:
                print("Неверный ввод, повторите.")

# ------------------------- ЗАПУСК -------------------------
if __name__ == "__main__":
    app = PiggyBankApp()
    app.run()