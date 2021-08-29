const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

// Setup the event listeners
{% if user.is_superuser %}
document.getElementById("deptadmin-insert-a").addEventListener(
    "click", e => show_user_insert_form(e, "deptadmin")
);
{% endif %}

document.getElementById("teacher-insert-a").addEventListener(
    "click", e => show_user_insert_form(e, "teacher")
);
document.getElementById("student-insert-a").addEventListener(
    "click", e => show_user_insert_form(e, "student")
);
setup_row_event_listeners(document);


function setup_row_event_listeners(target)
{
    for (let a of target.getElementsByClassName("deptadmin-update-a")) {
        a.addEventListener(
            "click", e => show_user_update_form(e, a.href, "deptadmin")
        );
    }
    for (let a of target.getElementsByClassName("teacher-update-a")) {
        a.addEventListener(
            "click", e => show_user_update_form(e, a.href, "teacher")
        );
    }
    for (let a of target.getElementsByClassName("student-update-a")) {
        a.addEventListener(
            "click", e => show_user_update_form(e, a.href, "student")
        );
    }
    for (let form of target.getElementsByClassName("user-accept-form")) {
        let url = form.getAttribute("action");
        let uid = url.substring(7, url.length - 7);
        form.addEventListener(
            "submit", e => user_accept(e, uid)
        );
    }
    for (let a of target.getElementsByClassName("user-delete-a")) {
        let url = a.getAttribute("href");
        let uid = url.substring(7, url.length - 7);
        a.addEventListener(
            "click", e => show_user_delete_form(e, uid)
        );
    }
    for (let form of target.getElementsByClassName("user-activate-form")) {
        let url = form.getAttribute("action");
        let uid = url.substring(7, url.length - 9);
        form.addEventListener(
            "submit", e => user_activate(e, uid)
        );
    }
    for (let form of target.getElementsByClassName("user-deactivate-form")) {
        let url = form.getAttribute("action");
        let uid = url.substring(7, url.length - 11);
        form.addEventListener(
            "submit", e => user_deactivate(e, uid)
        );
    }
}


// Modal setup

var modal = document.getElementById("modal");
var modal_content = document.getElementById("modal-content");
var modal_close = document.getElementById("modal-close");
modal_close.addEventListener("click", e => modal_hide());
// Close the modal if the user clicks outside modal_content
modal.addEventListener("click", e => {
    if (e.target == modal) {
        modal_hide();
    }
});

function modal_hide()
{
    modal.style.display = "none";
}

function modal_set_content(content)
{
    modal_content.replaceChildren(content);
}

function modal_show(content)
{
    modal_set_content(content);
    modal.style.display = "block";
}


// User insert

function show_user_insert_form(e, mode)
{
    var xhr = new XMLHttpRequest();
    if (!xhr) {
        return;
    }
    xhr.onreadystatechange = () => {
        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
            let form = xhr.responseXML.getElementById("base-form");
            form.addEventListener("submit", e => user_insert(e, mode, form));
            modal_show(form);
        }
    };
    xhr.open("GET", "/users/insert/" + mode);
    xhr.responseType = "document";  // Init the HTML parser
    xhr.send(null);
    e.preventDefault();
}

function user_insert(e, mode, form) {
    if (mode === "student") {
        var table_id = "student-table";
    } else if (mode === "teacher") {
        var table_id = "teacher-table";
    } else if (mode === "deptadmin") {
        var table_id = "deptadmin-table";
    }

    var xhr = new XMLHttpRequest();
    if (!xhr) {
        return;
    }
    xhr.onreadystatechange = () => {
        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
            let form = xhr.responseXML.getElementById("base-form");
            if (form == null) {
                let table = xhr.responseXML.getElementById(table_id);
                setup_row_event_listeners(table);
                document.getElementById(table_id).replaceWith(table);
                modal_hide();
                return;
            }
            form.addEventListener("submit", e => user_insert(e, mode, form));
            modal_set_content(form);
        }
    };
    xhr.open("POST", "/users/insert/" + mode);
    xhr.responseType = "document";  // Init the HTML parser
    xhr.send(new FormData(form));
    e.preventDefault();
}


// User update

function show_user_update_form(e, url, mode)
{
    var xhr = new XMLHttpRequest();
    if (!xhr) {
        return;
    }
    xhr.onreadystatechange = () => {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                let form = xhr.responseXML.getElementById("base-form");
                form.addEventListener(
                    "submit", e => user_update(e, url, mode, form)
                );
                modal_show(form);
            }
        }
    };
    xhr.open("GET", url);
    xhr.responseType = "document";  // Init the HTML parser
    xhr.send(null);
    e.preventDefault();
}

function user_update(e, url, mode, form) {
    if (mode === "student") {
        var table_id = "student-table";
    } else if (mode === "teacher") {
        var table_id = "teacher-table";
    } else if (mode === "deptadmin") {
        var table_id = "deptadmin-table";
    }

    var xhr = new XMLHttpRequest();
    if (!xhr) {
        return;
    }
    xhr.onreadystatechange = () => {
        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
            let form = xhr.responseXML.getElementById("base-form");
            if (form == null) {
                let table = xhr.responseXML.getElementById(table_id);
                setup_row_event_listeners(table);
                document.getElementById(table_id).replaceWith(table);
                modal_hide();
                return;
            }
            form.addEventListener(
                "submit", e => user_update(e, url, mode, form)
            );
            modal_set_content(form);
        }
    };
    xhr.open("POST", url);
    xhr.responseType = "document";  // Init the HTML parser
    xhr.send(new FormData(form));
    e.preventDefault();
}


// User delete

function show_user_delete_form(e, uid)
{
    var xhr = new XMLHttpRequest();
    if (!xhr) {
        return;
    }
    xhr.onreadystatechange = () => {
        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
            let form = xhr.responseXML.getElementById("confirm-form");
            form.addEventListener(
                "submit", e => user_delete(e, uid, form)
            );
            let a = xhr.responseXML.getElementById("confirm-form-return");
            a.addEventListener("click", e => {
                modal_hide();
                e.preventDefault();
            });
            modal_show(form);
        }
    };
    xhr.open("GET", "/users/" + uid + "/delete");
    xhr.responseType = "document";  // Init the HTML parser
    xhr.send(null);
    e.preventDefault();
}

function user_delete(e, uid, form)
{
    var xhr = new XMLHttpRequest();
    if (!xhr) {
        return;  // Let the input submit as a fallback
    }
    xhr.onreadystatechange = () => {
        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
            document.getElementById("user_" + uid).remove();
            modal_hide();
        }
    };
    xhr.open("POST", "/users/" + uid + "/delete");
    xhr.setRequestHeader("X-CSRFToken", csrftoken);
    xhr.responseType = "document";  // Init the HTML parser
    xhr.send(new FormData(form));
    e.preventDefault();  // Prevent the form from submitting
}


// User actions

function user_accept(e, uid)
{
    var xhr = new XMLHttpRequest();
    if (!xhr) {
        return;  // Let the input submit as a fallback
    }
    xhr.onreadystatechange = () => {
        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
            let tr = xhr.responseXML.getElementById("user_" + uid);
            document.getElementById("user_" + uid).replaceWith(tr);
            setup_row_event_listeners(tr);
        }
    };
    xhr.open("POST", "/users/" + uid + "/accept");
    xhr.responseType = "document";  // Init the HTML parser
    xhr.setRequestHeader("X-CSRFToken", csrftoken);
    xhr.send(null);
    e.preventDefault();  // Prevent the form from submitting
}


function user_activate(e, uid)
{
    var xhr = new XMLHttpRequest();
    if (!xhr) {
        return;  // Let the input submit as a fallback
    }
    xhr.onreadystatechange = () => {
        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
            let tr = xhr.responseXML.getElementById("user_" + uid);
            document.getElementById("user_" + uid).replaceWith(tr);
            setup_row_event_listeners(tr);
        }
    };
    xhr.open("POST", "/users/" + uid + "/activate");
    xhr.responseType = "document";  // Init the HTML parser
    xhr.setRequestHeader("X-CSRFToken", csrftoken);
    xhr.send(null);
    e.preventDefault();  // Prevent the form from submitting
}

function user_deactivate(e, uid)
{
    var xhr = new XMLHttpRequest();
    if (!xhr) {
        return;  // Let the input submit as a fallback
    }
    xhr.onreadystatechange = () => {
        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
            let tr = xhr.responseXML.getElementById("user_" + uid);
            document.getElementById("user_" + uid).replaceWith(tr);
            setup_row_event_listeners(tr);
        }
    };
    xhr.open("POST", "/users/" + uid + "/deactivate");
    xhr.responseType = "document";  // Init the HTML parser
    xhr.setRequestHeader("X-CSRFToken", csrftoken);
    xhr.send(null);
    e.preventDefault();  // Prevent the form from submitting
}
