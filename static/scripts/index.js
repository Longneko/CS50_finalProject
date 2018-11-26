// var card_container_prototype is imported from template
// function fetch_object is imported from fetch.js via template

const IMG_PATH = "static/images/";
const MSG_NO_MORE_MEALS = "There are no more recipes that fit your settings T_T";

var action_url = window.location.origin + "/action"; // URL to send meal add/remove commands
console.log(action_url); // DEBUG

active_meal_ids = []; // holds ids of meals/recipes in cards

// Return a string with sorted unique ingredient categories of recipe
function recipe_to_cat_str(recipe) {
    var unique_categories = new Set(recipe["contents"].map(c => c["ingredient"]["category"]["name"]));
    var sorted_categories = Array.from(unique_categories).sort();
    var categories_str = sorted_categories.join(", ");

    return categories_str
}

// Fetch a random valid recipe for a user and pass it to success callback func
// or pass -1 if no such recipes available
function get_random_valid_recipe(exclude_ids, data=null, success=null) {
    if ( data ) {
        var valid_ids = data.filter(id => exclude_ids.indexOf(id) < 0);
        if ( valid_ids.length == 0 ) {
            return success(-1); // if no more recipes left
        }

        var random_id = valid_ids[Math.floor(Math.random() * valid_ids.length)];

        fetch_object("recipe", random_id, function(data) {
           return success(data);
        });
    } else {
        fetch_object("valid_meals", null, function(data) {
            get_random_valid_recipe(exclude_ids, data, function(data) {
                success(data);
            });
        });
    }
}

// Add new meal to the user and add a card container to DOM using random valid meal
function add_meal(exclude_ids, next_card_id, data=null) {
    if ( data == -1 ) {
        alert(MSG_NO_MORE_MEALS);
    } else if ( data ) {
        var recipe = data;
        exclude_ids.push(recipe["id"]);

        // create an html string of a card col by replacing placeholders in the prototype
        var card_container = card_container_prototype;
        for ( pholder of ["%id%", "%name%"]) {
            card_container = card_container.split(pholder).join(recipe[pholder.substring(1, pholder.length - 1)]);
        }
        card_container = card_container.split("%categories%").join(recipe_to_cat_str(recipe));

        $("#" + next_card_id).parent().before(card_container);

        $("#meal-card-btn-reroll_" + recipe["id"]).click(function() {
            var recipe_id = $(this).prop("id").split("_").pop();
            var card_id = "meal-card_" + recipe_id;

            reroll_meal(card_id, active_meal_ids);
        });

        $("#meal-card-btn-accept_" + recipe["id"]).click(function() {
            var recipe_id = $(this).prop("id").split("_").pop();
            var card_id = "meal-card_" + recipe_id;

            accept_meal(card_id);
        });

        $("#meal-card-btn-remove_" + recipe["id"]).click(function() {
            var recipe_id = $(this).prop("id").split("_").pop();
            var card_id = "meal-card_" + recipe_id;

            remove_meal(card_id, active_meal_ids);
        });
    } else {
        get_random_valid_recipe(exclude_ids, null, function(data) {
            add_meal(exclude_ids, next_card_id, data);
        });
    }
}

// Change card contents to show another recipe
function update_card(card_id, recipe) {
    var old_recipe_id = $("#" + card_id).data("meal_id");
    var card = $("#" + card_id);

    // Update card contents and data
    $(card).data("meal_id", recipe["id"]);
    var new_img_src = $(card).find("[id^=meal-card-img]").prop("src").replace(old_recipe_id, recipe["id"]);
    $(card).find("[id^=meal-card-img]").prop("src", new_img_src);
    $(card).find("[id^=meal-card-header]").html(recipe["name"]);
    $(card).find("[id^=meal-card-categories]").html(recipe_to_cat_str(recipe));


    // update decendant elemets' ids with that of the new recipe
    var elements = $(card).find("*").add(card);
    for ( el of elements ) {
        try {
            var new_id = $(el).prop("id").replace(old_recipe_id, recipe["id"]);
            $(el).prop("id", new_id);
        } catch (e) {
        }
    }
}

// Reroll meal on a card
function reroll_meal(card_id, exclude_ids){
    var current_recipe_id = $("#" + card_id).data("meal_id")
    get_random_valid_recipe(exclude_ids, null, function(recipe) {
        if ( recipe != -1 ) {
            update_card(card_id, recipe);

            // replace rerolled recipe id in list of active ones
            var index = exclude_ids.indexOf(current_recipe_id);
            if (index > -1) {
                exclude_ids.splice(index, 1);
            }
            exclude_ids.push(recipe["id"]);
        } else {
            alert(MSG_NO_MORE_MEALS);
        }
    });
}

// Add meal to the user and accept corresponding meal container
function accept_meal(card_id) {
    var card = $("#" + card_id)
    var recipe_id = parseInt($(card).data("meal_id"));
    var data = {
        "command": "add_meal",
        "id": recipe_id,
    };

    $.post(action_url, data, function(response) {
        if ( response == "success" ) {
            $(card).find("[id^=meal-card-btn-reroll]").prop('disabled', true);
            $(card).find("[id^=meal-card-btn-accept]").prop('disabled', true);
        }
    });
}

// Remove meal from the user and remove corresponding meal container
function remove_meal(card_id, meal_ids) {
    var card = $("#" + card_id)
    var recipe_id = parseInt($(card).data("meal_id"));
    var data = {
        "command": "remove_meal",
        "id": recipe_id,
    };

    $.post(action_url, data, function(response) {
        if ( response == "success" ) {
            // remove recipe id from the list of active ones
            var index = meal_ids.indexOf(recipe_id);
            if (index > -1) {
                meal_ids.splice(index, 1);
            }
            $(card).parent().remove(); // removing parent because card is always wrapped in a div
        }
    });
}

$(document).ready(function() {
    var meal_cards = $("[id^=meal-card_")
    for ( card of meal_cards ) {
        active_meal_ids.push($(card).data("meal_id"));
    }

    $("#meal-card-img_add").click(function() {
        add_meal(active_meal_ids, "meal-card_add");
    });

    // accepted cards have disabled reroll buttons, so this is left 'just in case'
    $("[id^=meal-card-btn-reroll]").click(function() {
        var recipe_id = $(this).prop("id").split("_").pop();
        var card_id = "meal-card_" + recipe_id;

        reroll_meal(card_id, active_meal_ids);
    });

    // accepted cards have disabled accept buttons, so this is left 'just in case'
    $("[id^=meal-card-btn-accept]").click(function() {
        var recipe_id = $(this).prop("id").split("_").pop();
        var card_id = "meal-card_" + recipe_id;

        accept_meal(card_id);
    });

    $("[id^=meal-card-btn-remove]").click(function() {
        var recipe_id = $(this).prop("id").split("_").pop();
        var card_id = "meal-card_" + recipe_id;

        remove_meal(card_id, active_meal_ids);
    });
});
