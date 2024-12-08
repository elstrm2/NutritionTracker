# Nutrition Tracker Bot

## Description

The **Nutrition Tracker Bot** is a Telegram bot designed to help users track daily nutrition intake, including calories, proteins, fats, carbohydrates, and water. The bot also supports time zone and language adjustments, and calculates daily nutritional needs based on user-specific parameters.

[**Start using the Nutrition Tracker Bot**](https://t.me/nutrition_tracker_365_bot)

## Features

- Track calorie and water intake.
- Retrieve daily nutrition logs.
- Calculate daily nutritional needs.
- Multi-language support: English and Russian.
- Time zone management for accurate tracking.

## Commands

### `/start`

Initializes the bot and registers the user.

### `/set <calories> <protein> <fat> <carbs> <water>`

Sets daily nutritional targets for the user.

### `/food <grams_eaten> <protein_per_100g> <fat_per_100g> <carbs_per_100g> [comment]`

Logs a food entry with nutritional details.

### `/water <liters>`

Logs the amount of water consumed.

### `/log [date]`

Retrieves the user's food and water logs for a specific day.

### `/calc <age> <weight> <height> <metabolism> <activity> <goal> <desire> <diet_type> <gender> <body_fat> <climate> <rhr>`

Calculates personalized daily nutritional needs.

### `/time <timezone>`

Sets the user's time zone for accurate logging.

### `/lang <en/ru>`

Changes the bot's language between English and Russian.

### `/progress [date]`

Shows the user's daily progress towards nutritional goals.

### `/count`

Displays the total number of registered users.

### `/reset`

Resets the user's daily progress for the current day.

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License** (CC BY-NC-ND 4.0).

- **Attribution**: you must give appropriate credit, provide a link to the license, and indicate if changes were made.
- **Non-Commercial**: you may not use the material for commercial purposes.
- **No Derivatives**: if you remix, transform, or build upon the material, you may not distribute the modified material.

For the full license text, you can visit the [Creative Commons website](https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode) or see the `LICENSE` file in the project directory.
