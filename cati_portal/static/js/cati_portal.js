function delete_user(login, user_url) {
    if (confirm('Permanently delete user ' + login + ' ?') == true) {
        $.ajax({
            url: user_url,
            method: 'DELETE'
        })
         .done(function() {
            location.reload();
         })
        .fail(function (jqXHR) {
            document.open();
            document.write(jqXHR.responseText);
            document.close();
        })
    }
}

function validate_email(login, email, user_url, ask=false) {
    if (! ask || confirm('Force ' + email + ' validation for user ' + login + ' without email verification ?') == true) {
        $.ajax({
            url: user_url,
            method: 'PUT',
            data: {
                email_verification: true,
            }
        })
        .done(function() {
            location.reload();
        })
        .fail(function (jqXHR) {
            document.open();
            document.write(jqXHR.responseText);
            document.close();
        })
    }
}


function activate_user(login, user_url, ask=false) {
    if (! ask || confirm('Activate user '+ login + ' ?') == true) {
        $.ajax({
            url: user_url,
            method: 'PUT',
            data: {
                activation: true,
            }
        })
        .done(function() {
            location.reload();
        })
        .fail(function (jqXHR) {
            document.open();
            document.write(jqXHR.responseText);
            document.close();
        })
    }
}

function disable_user(login, user_url, ask=false) {
    if (! ask || confirm('Disable user '+ login + ' ?') == true) {
        $.ajax({
            url: user_url,
            method: 'PUT',
            data: {
                deactivation: true,
            }
        })
        .done(function() {
            location.reload();
        })
        .fail(function (jqXHR) {
            document.open();
            document.write(jqXHR.responseText);
            document.close();
        })
    }
}

function enable_user(login, user_url, ask=false) {
    if (! ask || confirm('Enable user '+ login + ' ?') == true) {
        $.ajax({
            url: user_url,
            method: 'PUT',
            data: {
                deactivation: false,
            }
        })
        .done(function() {
            location.reload();
        })
        .fail(function (jqXHR) {
            document.open();
            document.write(jqXHR.responseText);
            document.close();
        })
    }
}
