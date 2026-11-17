
from database import get_connection, init_db


# All nutrition values per 100 grams:
# (name, calories, protein, carbs, fat)

foods = [
    # ----------------------------------
    # POULTRY AND MEAT
    # ----------------------------------
    ("Chicken breast, raw", 120, 22.5, 0, 2.6),
    ("Chicken breast, cooked", 165, 31, 0, 3.6),
    ("Chicken thigh, raw, skinless", 119, 19.7, 0, 4.1),
    ("Turkey breast, raw", 114, 23.7, 0.1, 1.5),
    ("Turkey breast, cooked", 135, 29, 0, 1.6),
    ("Pork tenderloin, raw", 109, 20.9, 0, 2.2),
    ("Pork loin, raw", 143, 21.4, 0, 5.8),
    ("Pork chop, raw", 174, 20.7, 0, 9.5),
    ("Beef, lean, raw", 152, 21, 0, 7),
    ("Beef, lean, cooked", 217, 30, 0, 9),
    ("Beef ground, 80% lean, raw", 254, 17.2, 0, 20),
    ("Beef ground, 93% lean, raw", 172, 21.4, 0, 9.3),
    ("Lamb leg, lean, raw", 143, 20.5, 0, 6.7),

    # ----------------------------------
    # FISH AND SEAFOOD
    # ----------------------------------
    ("Tuna, canned in water, drained", 116, 25.5, 0, 0.8),
    ("Tuna, canned in oil, drained", 198, 29, 0, 8.2),
    ("Salmon, raw", 208, 20.4, 0, 13.4),
    ("Cod, raw", 82, 17.8, 0, 0.7),
    ("Hake, raw", 82, 17.8, 0, 0.7),
    ("Tilapia, raw", 96, 20.1, 0, 1.7),
    ("Shrimp, cooked", 99, 24, 0.2, 0.3),
    ("Mackerel, raw", 205, 18.6, 0, 13.9),
    ("Sardines, canned in oil, drained", 208, 24.6, 0, 11.5),
    ("Trout, raw", 141, 19.9, 0, 6.2),

    # ----------------------------------
    # EGGS AND DAIRY
    # ----------------------------------
    ("Egg, whole, raw", 143, 12.6, 0.7, 9.5),
    ("Egg, whole, boiled", 155, 12.6, 1.1, 10.6),
    ("Egg white, raw", 52, 10.9, 0.7, 0.2),
    ("Egg yolk, raw", 322, 15.9, 3.6, 26.5),
    ("Milk, whole", 61, 3.2, 4.8, 3.3),
    ("Milk, skimmed", 35, 3.4, 5, 0.1),
    ("Greek yogurt, plain, nonfat", 59, 10.3, 3.6, 0.4),
    ("Greek yogurt, plain, full fat", 97, 9, 3.9, 5),
    ("Skyr, plain", 63, 11, 4, 0.2),
    ("Cottage cheese, low fat", 82, 11.1, 3.4, 2.3),
    ("Quark, low fat", 67, 12, 4, 0.2),
    ("Yogurt, plain, low fat", 63, 5.3, 7, 1.6),
    ("Feta cheese", 264, 14.2, 4.1, 21.3),
    ("Mozzarella, part skim", 254, 24.3, 2.8, 15.9),
    ("Cheddar cheese", 403, 24.9, 1.3, 33.1),
    ("Parmesan cheese", 392, 35.8, 3.2, 25.8),
    ("Ricotta cheese, whole milk", 174, 11.3, 3, 13),
    ("Whey protein isolate, powder", 370, 85, 4, 2),

    # ----------------------------------
    # RICE, GRAINS AND PASTA
    # ----------------------------------
    ("White rice, dry", 365, 7.1, 80, 0.7),
    ("White rice, cooked", 130, 2.7, 28.2, 0.3),
    ("Brown rice, dry", 370, 7.5, 77.2, 2.9),
    ("Brown rice, cooked", 123, 2.7, 25.6, 1),
    ("Basmati rice, dry", 365, 7.1, 80, 0.7),
    ("Quinoa, dry", 368, 14.1, 64.2, 6.1),
    ("Quinoa, cooked", 120, 4.4, 21.3, 1.9),
    ("Oats, dry", 389, 16.9, 66.3, 6.9),
    ("Pasta, dry", 371, 13, 74.7, 1.5),
    ("Pasta, cooked", 158, 5.8, 30.9, 0.9),
    ("Couscous, dry", 376, 12.8, 77.4, 0.6),
    ("Couscous, cooked", 112, 3.8, 23.2, 0.2),
    ("Bulgur, cooked", 83, 3.1, 18.6, 0.2),
    ("Buckwheat, dry", 343, 13.3, 71.5, 3.4),
    ("Bread, whole wheat", 247, 13, 41, 4.2),
    ("Bread, white", 266, 8.9, 49.4, 3.3),
    ("Tortilla, wheat", 312, 8.3, 52.1, 8.3),

    # ----------------------------------
    # POTATOES AND STARCHES
    # ----------------------------------
    ("Potato, raw", 77, 2, 17, 0.1),
    ("Potato, boiled", 87, 1.9, 20.1, 0.1),
    ("Sweet potato, raw", 86, 1.6, 20.1, 0.1),
    ("Sweet potato, baked", 90, 2, 20.7, 0.2),
    ("Corn, sweet, cooked", 96, 3.4, 21, 1.5),

    # ----------------------------------
    # BEANS AND LEGUMES
    # ----------------------------------
    ("Lentils, dry", 352, 24.6, 63.4, 1.1),
    ("Lentils, cooked", 116, 9, 20.1, 0.4),
    ("Chickpeas, cooked", 164, 8.9, 27.4, 2.6),
    ("Kidney beans, cooked", 127, 8.7, 22.8, 0.5),
    ("Black beans, cooked", 132, 8.9, 23.7, 0.5),
    ("White beans, cooked", 139, 9.7, 25.1, 0.4),
    ("Green peas, cooked", 84, 5.4, 15.6, 0.2),
    ("Tofu, firm", 144, 17.3, 2.8, 8.7),
    ("Edamame, cooked", 121, 11.9, 8.9, 5.2),

    # ----------------------------------
    # OILS, NUTS AND FATS
    # ----------------------------------
    ("Olive oil", 884, 0, 0, 100),
    ("Sunflower oil", 884, 0, 0, 100),
    ("Butter, unsalted", 717, 0.9, 0.1, 81.1),
    ("Avocado, raw", 160, 2, 8.5, 14.7),
    ("Almonds, raw", 579, 21.2, 21.6, 49.9),
    ("Walnuts, raw", 654, 15.2, 13.7, 65.2),
    ("Peanuts, raw", 567, 25.8, 16.1, 49.2),
    ("Cashews, raw", 553, 18.2, 30.2, 43.8),
    ("Peanut butter, unsweetened", 588, 25, 20, 50),
    ("Chia seeds, dry", 486, 16.5, 42.1, 30.7),
    ("Flaxseeds, dry", 534, 18.3, 28.9, 42.2),
    ("Pumpkin seeds, dry", 559, 30.2, 10.7, 49.1),

    # ----------------------------------
    # VEGETABLES
    # ----------------------------------
    ("Tomato, raw", 18, 0.9, 3.9, 0.2),
    ("Broccoli, raw", 34, 2.8, 6.6, 0.4),
    ("Cauliflower, raw", 25, 1.9, 5, 0.3),
    ("Spinach, raw", 23, 2.9, 3.6, 0.4),
    ("Carrot, raw", 41, 0.9, 9.6, 0.2),
    ("Cucumber, raw", 15, 0.7, 3.6, 0.1),
    ("Bell pepper, red, raw", 31, 1, 6, 0.3),
    ("Onion, raw", 40, 1.1, 9.3, 0.1),
    ("Garlic, raw", 149, 6.4, 33.1, 0.5),
    ("Mushrooms, white, raw", 22, 3.1, 3.3, 0.3),
    ("Zucchini, raw", 17, 1.2, 3.1, 0.3),
    ("Eggplant, raw", 25, 1, 5.9, 0.2),
    ("Asparagus, raw", 20, 2.2, 3.9, 0.1),
    ("Lettuce, romaine, raw", 17, 1.2, 3.3, 0.3),
    ("Green beans, cooked", 35, 1.9, 7.9, 0.3),

    # ----------------------------------
    # FRUITS
    # ----------------------------------
    ("Banana, raw", 89, 1.1, 22.8, 0.3),
    ("Apple, raw", 52, 0.3, 13.8, 0.2),
    ("Orange, raw", 47, 0.9, 11.8, 0.1),
    ("Strawberries, raw", 32, 0.7, 7.7, 0.3),
    ("Blueberries, raw", 57, 0.7, 14.5, 0.3),
    ("Raspberries, raw", 52, 1.2, 11.9, 0.7),
    ("Mango, raw", 60, 0.8, 15, 0.4),
    ("Grapes, raw", 69, 0.7, 18.1, 0.2),
    ("Peach, raw", 39, 0.9, 9.5, 0.3),

    # ----------------------------------
    # OTHER COMMON INGREDIENTS
    # ----------------------------------
    ("Honey", 304, 0.3, 82.4, 0),
    ("Sugar, white", 387, 0, 100, 0),
    ("Cocoa powder, unsweetened", 228, 19.6, 57.9, 13.7),
    ("Dark chocolate, 70-85%", 598, 7.8, 45.9, 42.6),
    ("Tomato paste", 82, 4.3, 18.9, 0.5),
]



def seed_database():
    init_db()

    with get_connection() as conn:
        conn.executemany("""
            INSERT OR IGNORE INTO foods
            (name, calories, protein, carbs, fat)
            VALUES (?, ?, ?, ?, ?)
        """, foods)

    print("Database initialized and seeded.")


if __name__ == "__main__":
    seed_database()
