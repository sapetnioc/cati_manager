function delete_user(login, item_id) {
    if (confirm('Permanently delete user ' + login + ' ?') == true) {
        $.ajax('/user/' + login, {'method': 'DELETE'})
        .done(function() {
            $('#'+item_id).hide();
        })
        .fail(function (jqXHR) {
            document.open();
            document.write(jqXHR.responseText);
            document.close();
        })
    }
}

function validate_user(login, item_id, ask=false) {
    if (! ask || confirm('Force ' + login + ' validation without email verification ?') == true) {
        $.ajax('/user/' + login, {'method': 'PUT'})
        .done(function() {  
            $('#'+item_id).hide();
        })
        .fail(function (jqXHR) {
            document.open();
            document.write(jqXHR.responseText);
            document.close();
        })
    }
}
