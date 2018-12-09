// var template_card_container is imported from template
// var template_meal_details is imported from template
// function fetch_object is imported from fetch.js via template

const MSG_NO_MORE_MEALS = "There are no more recipes that fit your settings T_T";
const MEAL_DETAILS_CONTAINER_ID = "modal-meal-details-content";
const ADD_CARDS_BEFORE = "meal-card-container_add"; // id of the element before which new cards should be added

var action_url = window.location.origin + "/action"; // URL to send meal add/remove commands

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
function add_meal(exclude_ids, add_before_id, data=null) {
    if ( data == -1 ) {
        alert(MSG_NO_MORE_MEALS);
    } else if ( data ) {
        var recipe = data;
        exclude_ids.push(recipe["id"]);

        // create an html string of a card col by replacing placeholders in the template
        var card_container = template_card_container;
        for ( pholder of ["%id%", "%name%"]) {
            var key = pholder.substring(1, pholder.length - 1);
            card_container = card_container.split(pholder).join(recipe[key]);
        }
        card_container = card_container.split("%categories%").join(recipe_to_cat_str(recipe));

        $("#" + add_before_id).before(card_container);
    } else {
        get_random_valid_recipe(exclude_ids, null, function(data) {
            add_meal(exclude_ids, add_before_id, data);
        });
    }
}

// Change meal details modal contents to show another recipe
function update_meal_details(container_id, recipe) {
    var container = $("#" + container_id);

    // Update container data and contents
    $(container).find("[data-obj_id]").data("obj_id", recipe["id"]);

    // create an html string of a meal details by replacing placeholders in the template
    var details = template_meal_details;
    for ( pholder of ["%id%", "%name%", "%instructions%"]) {
        var key = pholder.substring(1, pholder.length - 1);
        try {
            html_str = (recipe[key]).replace(/(?:\r\n|\r|\n)/g, '<br>'); // Replace newline chars with <br> https://stackoverflow.com/a/784547/10491824
        } catch (err) {
            html_str = recipe[key];
        }
        details = details.split(pholder).join(html_str);
    }
    var contents_html = "";
    recipe["contents"].sort((a, b) => a["ingredient"]["name"].localeCompare(b["ingredient"]["name"]));  // sort contents by ingredient name https://stackoverflow.com/questions/1129216/sort-array-of-objects-by-string-property-value#comment20851078_1129270
    for ( c of recipe["contents"] ) {
        var ingredient_name = c["ingredient"]["name"];
        var ingredient_upper = ingredient_name.charAt(0).toUpperCase() + ingredient_name.slice(1);
        var amount = c["amount"] ? ( " - " + c["amount"] ) : "";
        var units = c["units"] ? ( " " + c["units"] ) : "";

        contents_html += "<li>" +  ingredient_upper + amount + units + "</li>\n";
    }
    details = details.split("%contents%").join(contents_html);

    $("#" + container_id).html(details);
}

// Change card contents to show another recipe
function update_card(card, recipe) {
    var card = $(card);
    var old_recipe_id = card.data("meal_id");

    // Update card data and contents
    card.data("meal_id", recipe["id"]);
    card.find("[data-obj_id]").data("obj_id", recipe["id"]);
    var img = card.find("[id^=meal-card-img]");
    img_change_file(img, recipe["id"]);
    card.find("[id^=meal-card-header]").html(recipe["name"]);
    card.find("[id^=meal-card-categories]").html(recipe_to_cat_str(recipe));


    // update decendant elemets' ids with that of the new recipe
    var elements = card.find("*").add(card);
    for ( el of elements ) {
        try {
            var new_id = $(el).prop("id").replace(old_recipe_id, recipe["id"]);
            $(el).prop("id", new_id);
        } catch (err) {
        }
    }
}

// Reroll meal on a card
function reroll_meal(card, exclude_ids, allow_repeat=false){
    var card = $(card);
    var current_recipe_id = card.data("meal_id");
    get_random_valid_recipe(exclude_ids, null, function(recipe) {
        if ( recipe != -1 ) {
            update_card(card, recipe);

            // replace rerolled recipe id in list of active ones if allow_repeat
            if ( allow_repeat ) {
                var index = exclude_ids.indexOf(current_recipe_id);
                if (index > -1) {
                    exclude_ids.splice(index, 1);
                }
            }
            exclude_ids.push(recipe["id"]);
        } else {
            alert(MSG_NO_MORE_MEALS);
        }
    });
}

// Add meal to the user and accept corresponding meal container
function accept_meal(card) {
    var card = $(card);
    var recipe_id = parseInt(card.data("meal_id"));
    var data = {
        "command": "add_meal",
        "id": recipe_id,
    };

    $.post(action_url, data, function(response) {
        if ( response == "success" ) {
            card.find("[id^=meal-card-btn-reroll]").prop('disabled', true);
            card.find("[id^=meal-card-btn-accept]").prop('disabled', true);
        }
    });
}

// Remove meal from the user and remove corresponding meal container
function remove_meal(card, meal_ids) {
    var card = $(card);
    var recipe_id = parseInt(card.data("meal_id"));
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
            card.parent().remove(); // removing parent because card is always wrapped in a div
        }
    });
}


function click_show_meal_details(e) {
    var recipe_id = $(e).data("obj_id");
    fetch_object("recipe", recipe_id, function(recipe){
        update_meal_details(MEAL_DETAILS_CONTAINER_ID, recipe);
    });
}

function click_card_remove(e) {
    var recipe_id = $(e).data("obj_id");
    var card = $("#meal-card_" + recipe_id);
    remove_meal(card, active_meal_ids);
}

function click_card_accept(e) {
    var recipe_id = $(e).data("obj_id");
    var card = $("#meal-card_" + recipe_id);
    accept_meal(card);
}

function click_card_reroll(e) {
    var recipe_id = $(e).data("obj_id");
    var card = $("#meal-card_" + recipe_id);
    reroll_meal(card, active_meal_ids);
}

function click_card_add() {
    add_meal(active_meal_ids, ADD_CARDS_BEFORE);
}

$(document).ready(function() {
    var meal_cards = $("[id^=meal-card_")
    for ( card of meal_cards ) {
        active_meal_ids.push($(card).data("meal_id"));
    }

    $("#meal-card-img_add").click(function() {
        add_meal(active_meal_ids, ADD_CARDS_BEFORE);
    });
    $("#meal-card-header_add").click(function() {
        add_meal(active_meal_ids, ADD_CARDS_BEFORE);
    });
});
