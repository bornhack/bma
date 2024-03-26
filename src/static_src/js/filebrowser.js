// getting some closure
"use strict";
(async function() {
    function BMAFileBrowser(container, messages, prefix) {
        // this ensures a clean object even if the new keyword is forgotten
        if (!(this instanceof BMAFileBrowser))  return new BMAFileBrowser(container, messages);

        // make $this always refer to this instance of BMAFileBrowser
        let $this = this;

        // save container, messages and prefix
        $this.container = container;
        $this.messages = messages;
        if (prefix) {
            $this.prefix = prefix + "-";
        } else {
            $this.prefix = "";
        };

        $this.baseUrl = window.location.protocol + "//" + window.location.host;


        $this.createNode = function(tag, classes, attrs, children) {
            let elem = document.createElement(tag);
            if (classes) {
                if (typeof classes === 'string') {
                    elem.className = classes;
                } else {
                    elem.className = classes.join(' ');
                };
            }
            if (attrs) {
                Object.assign(elem, attrs);
                // assign skips data- and hx- attributes for some reason, set them manually
                // TODO: maybe skip .assign() and do everything in the loop?
                for (const key in attrs) {
                    if (key.startsWith("data-") || key.startsWith("hx-")) {
                        elem.setAttribute(key, attrs[key]);
                    };
                };
            };
            if (children) {
                for (const child of children) {
                    elem.appendChild(child);
                };
            };
            return elem;
        };


        // select options in a multiselect
        $this.selectOptions = function(options, values) {
            options.forEach(function(o) {
                o.selected = false;
            });
            values.forEach(function(v) {
                options.forEach(function(o) {
                    if(o.value == v) {
                        o.selected = true;
                    };
                });
            });
        };


        // debounce multiple inputs
        $this.debounce = function(func, timeout = 300) {
            let timer;
            return (...args) => {
                clearTimeout(timer);
                timer = setTimeout(() => { func.apply(this, args); }, timeout);
            };
        };
        $this.processChange = $this.debounce(() => $this.updateFileBrowser());


        // the medium sized file template
        $this.getFileTemplate = function() {
            // the outer div
            const card = $this.createNode("div", ["card", "file"], {}, [
                // selected icon
                $this.createNode("span", ["position-absolute", "top-0", "end-0", "p-1", "bg-success", "border", "border-light", "selected-icon"], {}, [
                    $this.createNode("i", ["fas", "fa-check"]),
                ]),
                // selecting icon
                $this.createNode("span", ["position-absolute", "top-0", "end-0", "p-1", "bg-secondary", "border", "border-light", "selecting-icon"], {}, [
                    $this.createNode("i", ["fas", "fa-plus"]),
                ]),
                // thumbnail
                $this.createNode("img", "card-img-top"),
                // body
                $this.createNode("div", ["file-title", "card-body", "p-1"], {}, [
                    $this.createNode("span", ["small", "title"]),
                ]),
                // footer
                $this.createNode("div", ["file-info", "card-footer", "p-1", "d-inline-flex", "align-items-center", "justify-content-evenly"], {}, [
                    $this.createNode("i", "filetype", {"data-toggle": "tooltip", "data-placement": "bottom"}),
                    $this.createNode("i", "status", {"data-toggle": "tooltip", "data-placement": "bottom"}),
                    $this.createNode("span", ["badge", "text-bg-dark"], {"data-toggle": "tooltip", "data-placement": "bottom"}),
                ]),
            ]);

            // disco
            return card;
        };


        // getfiles function
        $this.getFiles = async function() {
            // start building url
            let url = new URL($this.baseUrl);
            url.pathname = "/api/v1/json/files/";

            // get filetypes element
            let el = $this.container.querySelector("select[name='" + $this.prefix + "type']");
            if (el.selectedOptions.length) {
                // filter by filetype
                const filetypes = Array.from(el.selectedOptions).map(v=>v.value);
                let t;
                for (t of filetypes) {
                    url.searchParams.append("filetypes", t);
                };
            };

            // get filestatus element
            el = $this.container.querySelector("select[name='" + $this.prefix + "status']");
            if (el.selectedOptions.length) {
                // filter by file status
                const statuses = Array.from(el.selectedOptions).map(v=>v.value);
                for (const s of statuses) {
                    url.searchParams.append("statuses", s);
                };
            };

            // get license element
            el = $this.container.querySelector("select[name='" + $this.prefix + "license']");
            if (el.selectedOptions.length) {
                // filter by file license
                const licenses = Array.from(el.selectedOptions).map(v=>v.value);
                for (const l of licenses) {
                    url.searchParams.append("licenses", l);
                };
            };

            // get search element
            el = $this.container.querySelector("input[name='" + $this.prefix + "search']");
            if (el.value) {
                // filter by title/description search
                url.searchParams.append("search", el.value);
            };


            $this.log("getting files with url: " + url);
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error, status = ${response.status}`);
            }
            return await response.json();
        };


        // update summary
        $this.updateSummary = async function(e, selected, unselected) {
            selected = $this.container.querySelectorAll("div.file.ui-selected");
            if (selected.length) {
                // at least 1 file is selected
                let size = 0;
                let counts = {
                    "picture": 0,
                    "video": 0,
                    "audio": 0,
                    "document": 0,
                };
                selected.forEach(function(file) {
                    size += parseInt(file.dataset.bmaFileSize);
                    counts[file.dataset.bmaFileType] += 1;
                });
                $this.container.querySelector("div.selection > .card-body").innerHTML = size + " bytes in " + selected.length + " files.<br>" + counts["picture"] + " pictures, " + counts["video"] + " videos, " + counts["audio"] + " audios, " + counts["document"] + " documents.";
                let buttons = $this.container.querySelectorAll("div.btn-group.actions > button");
                for (const button of buttons) {
                    button.removeAttribute("disabled");
                };
            } else {
                // selection is empty
                $this.container.querySelector("div.selection > .card-body").innerHTML = "0 bytes in 0 files<br>0 pictures, 0 videos, 0 audios, 0 documents.";
                let buttons = $this.container.querySelectorAll("div.btn-group.actions > button");
                for (const button of buttons) {
                    button.setAttribute("disabled", "");
                };
                $('[data-toggle="tooltip"]').tooltip("hide");
            };
        };


        // set form values from URL queryset
        $this.updateFormFromUrl = function(form) {
            // populate initial values
            const url = new URL(window.location);

            // get initial search value
            form.querySelector("input[name='" + $this.prefix + "search']").value = url.searchParams.get($this.prefix + "search");

            // get initial filetypes
            let options = Array.from(form.querySelectorAll("select[name='" + $this.prefix + "type'] > option"));
            let values = url.searchParams.getAll($this.prefix + "type");
            $this.selectOptions(options, values);

            // get initial filestatus
            options = Array.from(form.querySelectorAll("select[name='" + $this.prefix + "status'] > option"));
            values = url.searchParams.getAll($this.prefix + "status");
            $this.selectOptions(options, values);

            // get initial licenses
            options = Array.from(form.querySelectorAll("select[name='" + $this.prefix + "license'] > option"));
            values = url.searchParams.getAll($this.prefix + "license");
            $this.selectOptions(options, values);
        };


        // createFileBrowser function
        $this.createFileBrowser = async function() {
            // create outer and wrapper divs
            const outer = $this.createNode("div", "filebrowser-container");
            const toolbar = $this.createNode("div", "btn-toolbar");
            outer.appendChild(toolbar);
            const fluid = $this.createNode("div", "container-fluid");
            toolbar.appendChild(fluid);
            const nav = $this.createNode("div", ["navbar", "bg-light", "p-2", "pe-0", "border"]);
            fluid.appendChild(nav);

            // create form
            const fg = $this.createNode("div", ["form-group", "me-2", "h-25", "border", "p-2"]);
            nav.appendChild(fg);
            const form = $this.createNode("form", ["row", "gy-2", "gx-3", "align-items-center"], );
            form.setAttribute("onsubmit", "return false;");

            // filetype select
            const ftcol = $this.createNode("div", "col-auto");
            const ftsel = $this.createNode("select", "form-select", {"name": $this.prefix + "type", "multiple": "multiple", "onchange": $this.updateFileBrowser}, [
                $this.createNode("option", [], {"value": "picture", "text": "Picture"}),
                $this.createNode("option", [], {"value": "video", "text": "Video"}),
                $this.createNode("option", [], {"value": "audio", "text": "Audio"}),
                $this.createNode("option", [], {"value": "document", "text": "Document"}),
            ]);
            ftcol.appendChild(ftsel);
            form.appendChild(ftcol);

            // filestatus select
            const fscol = $this.createNode("div", "col-auto");
            const fssel = $this.createNode("select", "form-select", {"name": $this.prefix + "status", "multiple": "multiple", "onchange": $this.updateFileBrowser}, [
                $this.createNode("option", [], {"value": "PENDING_MODERATION", "text": "Pending Moderation"}),
                $this.createNode("option", [], {"value": "UNPUBLISHED", "text": "Unpublished"}),
                $this.createNode("option", [], {"value": "PUBLISHED", "text": "Published"}),
                $this.createNode("option", [], {"value": "PENDING_DELETION", "text": "Pending Deletion"}),
            ]);
            fscol.appendChild(fssel);
            form.appendChild(fscol);

            // file license select
            const flcol = $this.createNode("div", "col-auto");
            const flsel = $this.createNode("select", "form-select", {"name": $this.prefix + "license", "multiple": "multiple", "onchange": $this.updateFileBrowser}, [
                $this.createNode("option", [], {"value": "CC_ZERO_1_0", "text": "Creative Commons CC0 1.0 Universal"}),
                $this.createNode("option", [], {"value": "CC_BY_4_0", "text": "Creative Commons Attribution 4.0 International"}),
                $this.createNode("option", [], {"value": "CC_BY_SA_4_0", "text": "Creative Commons Attribution-ShareAlike 4.0 International"}),
            ]);
            flcol.appendChild(flsel);
            form.appendChild(flcol);

            // search
            const searchcol = $this.createNode("div", "col-auto", {}, [
                $this.createNode("input", [], {"name": $this.prefix + "search", "placeholder": "search...", "onchange": $this.processChange}),
            ]);
            form.appendChild(searchcol);

            // set initial form values from url
            $this.updateFormFromUrl(form);

            // form done
            fg.appendChild(form);
            nav.appendChild(fg);

            // totals
            const totals = $this.createNode("div", ["card", "border", "me-2", "totals"], {}, [
                $this.createNode("div", "card-header", {"innerHTML": "Totals"}),
                $this.createNode("div", "card-body", {"innerHTML": "0 bytes in 0 files<br>0 pictures, 0 videos, 0 audios, 0 documents."}),
            ]);
            nav.appendChild(totals);

            // selection and actions
            const selection = $this.createNode("div", ["card", "border", "me-2", "selection"], {}, [
                $this.createNode("div", "card-header", {"innerHTML": "Selection"}, [
                    $this.createNode("div", ["btn-group", "me-2", "actions", "float-end"], {}, [
                        $this.createNode("button", ["btn", "btn-success"], {"data-toggle": "tooltip", "title": "Approve Files", "data-bs-toggle": "modal", "data-bs-target": "#" + $this.prefix + "bma-modal", "data-bma-action": "Approve Files", "disabled": "disabled"}, [
                            $this.createNode("i", ["fa-solid", "fa-check"]),
                        ]),
                        $this.createNode("button", ["btn", "btn-success"], {"data-toggle": "tooltip", "title": "Publish Files", "data-bs-toggle": "modal", "data-bs-target": "#" + $this.prefix + "bma-modal", "data-bma-action": "Publish Files", "disabled": "disabled"}, [
                            $this.createNode("i", ["fa-solid", "fa-cloud-arrow-up"]),
                        ]),
                        $this.createNode("button", ["btn", "btn-danger"], {"data-toggle": "tooltip", "title": "Unpublish Files", "data-bs-toggle": "modal", "data-bs-target": "#" + $this.prefix + "bma-modal", "data-bma-action": "Unpublish Files", "disabled": "disabled"}, [
                            $this.createNode("i", ["fa-solid", "fa-cloud-arrow-down"]),
                        ]),
                        $this.createNode("button", ["btn", "btn-primary"], {"data-toggle": "tooltip", "title": "Add Files To Album", "data-bs-toggle": "modal", "data-bs-target": "#" + $this.prefix + "bma-modal", "data-bma-action": "Add Files To Album", "disabled": "disabled"}, [
                            $this.createNode("i", ["fa-solid", "fa-plus"]),
                        ]),
                    ]),
                ]),
                $this.createNode("div", "card-body", {"innerHTML": "0 bytes in 0 files<br>0 pictures, 0 videos, 0 audios, 0 documents."}),
            ]);
            nav.appendChild(selection);

            const deck = $this.createNode("div", ["file-container", "d-flex", "align-content-start", "flex-wrap"]);
            outer.append(deck);

            // ok, add to the container
            $this.container.append(outer);

            // enable tooltips
            $('[data-toggle="tooltip"]').tooltip();

            // create action modal
            $this.actionmodal = $this.createNode("div", ["modal"], {"id": $this.prefix + "bma-modal", "tabindex": "-1"});
            $this.populateActionModal();

            const actions = {
                "Approve Files": "/api/v1/json/files/approve/",
                "Publish Files": "/api/v1/json/files/publish/",
                "Unpublish Files": "/api/v1/json/files/unpublish/",
            };

            $this.actionmodal.addEventListener('show.bs.modal', async event => {
                $('[data-toggle="tooltip"]').tooltip("hide");
                const button = event.relatedTarget;
                // TODO blur() doesn't work, button still has focus after modal is hidden
                button.blur();
                const action = button.getAttribute('data-bma-action');
                const selected = $this.container.querySelectorAll("div.file.ui-selected");
                if (!selected.length) {
                    throw new Error("No files selected!");
                };
                const filelist = $this.createNode("ul");
                const uuids = [];
                selected.forEach(file => {
                    filelist.appendChild($this.createNode("li", [], {"textContent": file.dataset.bmaFileName}));
                    uuids.push(file.dataset.bmaFileUuid);
                });

                $this.actionmodal.querySelector("div.modal-body").replaceChildren(filelist);

                // make check request
                const url = new URL($this.baseUrl);
                url.pathname = actions[action];
                url.searchParams.append("check", "true");
                const response = await fetch(url, {"method": "PATCH", "body": JSON.stringify({"files": uuids}), "headers": {"x-csrftoken": $this.getCsrfToken()}});
                if (response.ok) {
                    $this.actionmodal.querySelector("h1").textContent = "Really " + action + "?";
                    $this.actionmodal.querySelector("button.btn-primary").setAttribute("hx-patch", actions[action]);
                    $this.actionmodal.querySelector("button.btn-primary").setAttribute("hx-vals", JSON.stringify({"files": uuids}));
                    $this.actionmodal.querySelector("button.btn-primary").classList.remove("d-none");
                    htmx.process($this.actionmodal);
                } else {
                    $this.actionmodal.querySelector("h1").textContent = "Unable to " + action + "!";
                    console.log(await response.json());
                };
            })
            $this.actionmodal.addEventListener('hide.bs.modal', async event => {
                // reset the modal and update filebrowser
                $this.populateActionModal();
                $this.updateFileBrowser();
            });
            document.querySelector("body").appendChild($this.actionmodal);
        };


        // called to create and reset the action modal
        $this.populateActionModal = function() {
            $this.actionmodal.replaceChildren(
                $this.createNode("div", ["modal-dialog", "modal-dialog-scrollable"], {}, [
                    $this.createNode("div", "modal-content", {}, [
                        $this.createNode("div", "modal-header", {}, [
                            $this.createNode("h1", ["modal-title", "fs-5"]),
                            $this.createNode("button", "btn-close", {"data-bs-dismiss": "modal", "aria-label": "Close"}),
                        ]),
                        $this.createNode("div", "modal-body", {"id": $this.prefix + "modal-body"}),
                        $this.createNode("div", "modal-footer", {}, [
                            $this.createNode("button", ["btn", "btn-secondary"], {"textContent": "Cancel", "data-bs-dismiss": "modal"}),
                            $this.createNode("button", ["btn", "btn-primary", "d-none"], {"textContent": "Confirm", "hx-target": "closest div.modal-footer", "hx-swap": "innerHTML"}),
                        ]),
                    ]),
                ]),
            );
        };


        // return the csrf token from the body tag
        $this.getCsrfToken = function() {
            return JSON.parse(document.querySelector("body").getAttribute("hx-headers"))["x-csrftoken"]
        };


        // log a message with the filebrowsers id as prefix
        $this.log = function(message) {
            console.log($this.container.id + ": " + message);
        };


        // update the browser urlbar
        $this.updateUrl = function() {
            const formData = new FormData($this.container.querySelector("form"));
            const urlParams = new URLSearchParams(formData);
            const url = new URL(window.location);
            ["type", "status", "license", "search"].forEach(function(key) {
                key = $this.prefix + key;
                url.searchParams.delete(key);
            });
            urlParams.forEach(function(value, key) {
                if (value) {
                    url.searchParams.append(key, value);
                };
            });
            window.history.pushState(null, '', url.toString());
        };


        // disable the filter form
        $this.disableForm = function() {
            $this.container.querySelectorAll("form > div > select, form > div > input").forEach(function(e) {
                e.setAttribute("disabled", "disabled");
            });
        };

        // enable the filter form
        $this.enableForm = function() {
            $this.container.querySelectorAll("form > div > select, form > div > input").forEach(function(e) {
                e.removeAttribute("disabled");
            });
        };


        // update the files shown in the filebrowser
        $this.updateFileBrowser = async function(updateUrl) {
            // get or initiate filebrowser as needed
            let outer = $this.container.querySelector(".filebrowser-container");
            if (!outer) {
                $this.createFileBrowser();
                outer = $this.container.querySelector(".filebrowser-container");
            };

            if (updateUrl) {
                // update browser location to match form contents
                $this.updateUrl();
            };

            // disable form
            $this.disableForm();

            // get files from server
            $this.updateStatus("Getting data...", true);
            let response = await $this.getFiles();
            let data = response.bma_response;
            $this.updateStatus("Processing " + data.length + " files...", true);

            // remove files that are in the filebrowser but not in the json
            if (outer.querySelector("div.card")) {
                $this.updateStatus("Removing files...", true);
                let uuids = [];
                let file;
                //console.log(typeof(data));
                //console.log(data);
                for (file in data) {
                    console.log("processing file " + file);
                    uuids.push(data[file]["uuid"]);
                };
                let files = outer.querySelectorAll("div.file");
                files.forEach(function(existing) {
                    if (!uuids.includes(existing.dataset.bmaFileUuid)) {
                        existing.remove();
                    };
                });
            };
            let deck = outer.querySelector("div.file-container");

            // loop over files and add each
            $this.updateStatus("Adding files...", true);
            let size = 0;
            let counts = {
                "picture": 0,
                "video": 0,
                "audio": 0,
                "document": 0,
            };
            for (const file in data) {
                size += parseInt(data[file]["size_bytes"]);
                counts[data[file]["filetype"]] += 1;
                let existing = outer.querySelector("div[data-bma-file-uuid='" + data[file]["uuid"] + "']");
                if (existing) {
                    if (existing.dataset.bmaFileLastUpdate == data[file]["updated"]) {
                        // file has not been updated
                        continue;
                    } else {
                        // file has been updated
                        existing.remove();
                    };
                };
                let template = $this.getFileTemplate();
                let clone = template.cloneNode(true);
                // set title and thumbnail
                clone.querySelector(".title").innerHTML = data[file]["title"];
                clone.querySelector("img").src = data[file]["thumbnail_url"];
                // set footer icon for filetype
                let fi = clone.querySelector(".card-footer.file-info > i.filetype");
                fi.className = data[file]["filetype_icon"];
                fi.setAttribute("title", data[file]["filetype"]);
                // set footer icon for file status
                fi = clone.querySelector(".card-footer.file-info > i.status");
                fi.className = "status " + data[file]["status_icon"];
                fi.setAttribute("title", data[file]["status"]);
                // set footer icon for album count
                fi = clone.querySelector(".card-footer.file-info > span");
                fi.innerHTML = data[file]["albums"].length;
                fi.setAttribute("title", "This " + data[file]["filetype"] + " is in " + data[file]["albums"].length + " albums");
                // add file metadata attributes
                clone.dataset.bmaFileUuid=data[file]["uuid"];
                clone.dataset.bmaFileLastUpdate=data[file]["updated"];
                clone.dataset.bmaFileSize=data[file]["size_bytes"];
                clone.dataset.bmaFileType=data[file]["filetype"];
                clone.dataset.bmaFileName=data[file]["title"];
                clone.dataset.bmaFilePermissions=data[file]["effective_permissions"];
                deck.append(clone);
                // add this file to selectable
                $this.container._selectable.add(clone);
            };
            // update all the footer icon tooltips
            $('[data-toggle="tooltip"]').tooltip();

            $this.container.querySelector("div.totals > .card-body").innerHTML = size + " bytes in " + data.length + " files.<br>" + counts["picture"] + " pictures, " + counts["video"] + " videos, " + counts["audio"] + " audios, " + counts["document"] + " documents.";
            $this.updateSummary();
            $this.updateStatus("Ready. Showing " + $this.container.querySelectorAll("div.file").length + " files.");
            // enable form
            $this.enableForm();
        };


        // update statusbar
        $this.updateStatus = function(message, busy) {
            if (busy) {
                $this.messages.innerHTML="<i class='fas fa-spinner fa-spin'></i> ";
            } else {
                $this.messages.innerHTML="<i class='fas fa-circle fa-beat-fade'></i> ";
            };
            $this.messages.innerHTML+=message;
        };


        // init function
        $this.init = function() {
            // make sure Selectable is loaded
            if ( window.Selectable && typeof Selectable === "function" ) {
                // get the container
                if ( $this.container ) {
                    $this.updateStatus("Initialising Selectable for " + $this.container.id + "...", true);
                    const selectable = new Selectable({
                        appendTo: $this.container,
                        filter: $this.container.querySelectorAll(".card"),
                        ignore: ".navbar",
                    });
                    // attach the event listener
                    selectable.on('end', $this.updateSummary);
                    $this.updateStatus("Done initialising Selectable for " + $this.container.id + "!", true);
                } else {
                    throw "container not found";
                };
            } else {
                throw "Selectable not found";
            };
            // render initial contents
            $this.updateFileBrowser();

            // update filebrowser when browser back/forward buttons are used
            window.addEventListener('popstate', (event) => {
                $this.log(`Location changed by browser, updating form and filebrowser, new location: ${document.location}, state: ${JSON.stringify(event.state)}`);
                // set form values from url
                $this.updateFormFromUrl($this.container.querySelector("form"));
                // update filebrowser
                $this.updateFileBrowser(false);
            });
        };

        $this.init();
    };

    // function to initialise filebrowsers on the page
    async function bma_create_filebrowsers() {
        let containers = document.querySelectorAll(".filebrowser");
        if ( containers ) {
            // loop over containers and make them filebrowsers
            let i = 0;
            for (const container of containers) {
                i += 1;
                let body = document.getElementById(container.dataset.body);
                let messages = document.getElementById(container.dataset.messages);
                let prefix = "";
                if ( body && messages ) {
                    // initialise filebrowser
                    if (i > 1) {
                        // all but the first filebrowser gets a prefix for url parameters
                        prefix = "fb" + i;
                    };
                    console.log("Initialising BMA filebrowser...");
                    container._filebrowser = new BMAFileBrowser(body, messages, prefix);
                    console.log("Done initialised BMA filebrowser!");
                } else {
                    throw new Error("body or status element not found");
                };
            };
        } else {
            console.log("BMA filebrowser did not find any containers with the .filebrowser class");
        };
    };
    window.bma_create_filebrowsers = bma_create_filebrowsers;
})();

// create filebrowsers when the dom has finished loading
document.addEventListener("DOMContentLoaded", bma_create_filebrowsers);
