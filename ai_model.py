def predict_category(text):
    text = text.lower()

    if any(word in text for word in ["fan", "light", "electricity"]):
        return "Electrical ⚡"

    elif any(word in text for word in ["water", "leak", "drinking"]):
        return "Water 💧"

    elif any(word in text for word in ["wifi", "internet", "network"]):
        return "Network 📶"

    elif any(word in text for word in ["computer", "system", "lab"]):
        return "Computer Lab 💻"

    elif any(word in text for word in ["washroom", "toilet", "clean"]):
        return "Cleanliness 🧹"

    elif any(word in text for word in ["door", "window", "lock"]):
        return "Infrastructure 🏫"

    return "Other 📌"

def estimate_resolution(category):

    if "Electrical" in category:
        return "2 Days"

    elif "Water" in category:
        return "1 Day"

    elif "Network" in category:
        return "4 Hours"

    elif "Computer Lab" in category:
        return "1 Day"

    elif "Cleanliness" in category:
        return "Same Day"

    elif "Infrastructure" in category:
        return "3 Days"

    return "Under Review"


def predict_priority(text):
    text = text.lower()

    if any(word in text for word in ["fire", "danger", "leak", "urgent"]):
        return "High 🚨"

    elif any(word in text for word in ["broken", "damage", "not working"]):
        return "Medium ⚠️"

    return "Low 🟢"


def check_duplicate(new_text, old_complaints):

    new_text = new_text.lower().strip()

    for complaint in old_complaints:

        old_text = complaint["description"].lower().strip()

        # Exact same complaint
        if new_text == old_text:
            return True

        # Very similar complaint
        new_words = set(new_text.split())
        old_words = set(old_text.split())

        common_words = new_words.intersection(old_words)

        if len(common_words) >= 5:
            return True

    return False