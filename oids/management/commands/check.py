from oids.models import Trip, WorkRequestItem

# Перевіряємо, скільки елементів ВЗАГАЛІ не мають зв'язку з відрядженням
items_without_trip = WorkRequestItem.objects.filter(deadline_trigger_trip__isnull=True).count()
print(f"Знайдено елементів без зв'язку з відрядженням: {items_without_trip}")

# Перевіряємо, скільки елементів МАЮТЬ зв'язок
items_with_trip = WorkRequestItem.objects.filter(deadline_trigger_trip__isnull=False).count()
print(f"Знайдено елементів зі зв'язком з відрядженням: {items_with_trip}")

# Давайте подивимось на останнє створене відрядження
last_trip = Trip.objects.last()
if last_trip:
    print(f"\n--- Деталі останнього відрядження (ID: {last_trip.id}) ---")
    # Показуємо заявки, пов'язані з ним
    print("Пов'язані Заявки:")
    for wr in last_trip.work_requests.all():
        print(f"- {wr}")

    # Показуємо ОІДи, пов'язані з ним
    print("\nПов'язані ОІДи:")
    for oid in last_trip.oids.all():
        print(f"- {oid}")
else:
    print("Відряджень у базі даних не знайдено.")