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
                    $this.createNode("i", "filetype"),
                    $this.createNode("i", "status"),
                    $this.createNode("span", ["badge", "text-bg-dark"]),
                ]),
            ]);

            // disco
            return card;
        };

        // getfiles function
        $this.getFiles = async function() {
            // start building url
            let url = new URL(window.location.protocol + "//" + window.location.host + "/api/v1/json/files/");

            // get filetypes element
            let el = $this.container.querySelector("select[name='" + $this.prefix + "filetype']");
            if (el.selectedOptions.length) {
                // filter by filetype
                const filetypes = Array.from(el.selectedOptions).map(v=>v.value);
                let t;
                for (t of filetypes) {
                    url.searchParams.append("filetypes", t);
                };
            };

            // get filestatus element
            el = $this.container.querySelector("select[name='" + $this.prefix + "filestatus']");
            if (el.selectedOptions.length) {
                // filter by file status
                const statuses = Array.from(el.selectedOptions).map(v=>v.value);
                for (const s of statuses) {
                    url.searchParams.append("statuses", s);
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
                $this.container.querySelector("div.selection > .card-body").innerHTML = "0 bytes in 0 files<br>0 pictures, 0 videos, 0 audios, 0 documents.";
                let buttons = $this.container.querySelectorAll("div.btn-group.actions > button");
                for (const button of buttons) {
                    button.setAttribute("disabled", "");
                };
            };

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
            const ftsel = $this.createNode("select", "form-select", {"name": $this.prefix + "filetype", "multiple": "multiple", "onchange": $this.updateFileBrowser}, [
                $this.createNode("option", [], {"value": "Picture", "text": "Picture"}),
                $this.createNode("option", [], {"value": "Video", "text": "Video"}),
                $this.createNode("option", [], {"value": "Audio", "text": "Audio"}),
                $this.createNode("option", [], {"value": "Document", "text": "Document"}),
            ]);
            ftcol.appendChild(ftsel);
            form.appendChild(ftcol);

            // filestatus select
            const fscol = $this.createNode("div", "col-auto");
            const fssel = $this.createNode("select", "form-select", {"name": $this.prefix + "filestatus", "multiple": "multiple", "onchange": $this.updateFileBrowser}, [
                $this.createNode("option", [], {"value": "PENDING_MODERATION", "text": "Pending Moderation"}),
                $this.createNode("option", [], {"value": "UNPUBLISHED", "text": "Unpublished"}),
                $this.createNode("option", [], {"value": "PUBLISHED", "text": "Published"}),
                $this.createNode("option", [], {"value": "PENDING_DELETION", "text": "Pending Deletion"}),
            ]);
            fscol.appendChild(fssel);
            form.appendChild(fscol);

            // search
            const searchcol = $this.createNode("div", "col-auto", {}, [
                $this.createNode("input", [], {"name": $this.prefix + "search", "placeholder": "search...", "onchange": $this.processChange}),
            ]);
            form.appendChild(searchcol);

            // populate initial values
            const url = new URL(window.location);

            // get initial search value
            form.querySelector("input[name='" + $this.prefix + "search']").value = url.searchParams.get($this.prefix + "search");

            // get initial filetypes
            let options = Array.from(form.querySelectorAll("select[name='" + $this.prefix + "filetype'] > option"));
            let values = url.searchParams.getAll($this.prefix + "filetype");
            $this.selectOptions(options, values);

            // get initial filestatus
            options = Array.from(form.querySelectorAll("select[name='" + $this.prefix + "filestatus'] > option"));
            values = url.searchParams.getAll($this.prefix + "filestatus");
            $this.selectOptions(options, values);

            // form done
            fg.appendChild(form);
            nav.appendChild(fg);

            // totals
            const totals = $this.createNode("div", ["card", "border", "me-2", "totals"], {}, [
                $this.createNode("div", "card-header", {"innerHTML": "Totals"}),
                $this.createNode("div", "card-body", {"innerHTML": "0 bytes in 0 files<br>0 pictures, 0 videos, 0 audios, 0 documents."}),
            ]);
            nav.appendChild(totals);

            // selection
            const selection = $this.createNode("div", ["card", "border", "me-2", "selection"], {}, [
                $this.createNode("div", "card-header", {"innerHTML": "Selection"}, [
                    $this.createNode("div", ["btn-group", "me-2", "actions", "float-end"], {}, [
                        $this.createNode("button", ["btn", "btn-success"], {"disabled": "disabled"}, [
                            $this.createNode("i", ["fa-solid", "fa-cloud-arrow-up"]),
                        ]),
                        $this.createNode("button", ["btn", "btn-danger"], {"disabled": "disabled"}, [
                            $this.createNode("i", ["fa-solid", "fa-cloud-arrow-down"]),
                        ]),
                        $this.createNode("button", ["btn", "btn-primary"], {"disabled": "disabled"}, [
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
        };

        $this.log = function(message) {
            console.log($this.container.id + ": " + message);
        };

        $this.updateUrl = function() {
            const formData = new FormData($this.container.querySelector("form"));
            const urlParams = new URLSearchParams(formData);
            const url = new URL(window.location);
            urlParams.forEach(function(value, key) {
                url.searchParams.delete(key);
            });
            urlParams.forEach(function(value, key) {
                if (value) {
                    url.searchParams.append(key, value);
                };
            });
            window.history.pushState(null, '', url.toString());
        };

        $this.disableForm = function() {
            $this.container.querySelectorAll("form > div > select, form > div > input").forEach(function(e) {
                e.setAttribute("disabled", "disabled");
            });
        };

        $this.enableForm = function() {
            $this.container.querySelectorAll("form > div > select, form > div > input").forEach(function(e) {
                e.removeAttribute("disabled");
            });
        };

        // updateFileBrowser function
        $this.updateFileBrowser = async function() {
            // get or initiate filebrowser as needed
            let outer = $this.container.querySelector(".filebrowser-container");
            if (!outer) {
                $this.createFileBrowser();
                outer = $this.container.querySelector(".filebrowser-container");
            };

            // update browser location to match form contents
            $this.updateUrl();

            // disable form
            $this.disableForm();

            // get files from server
            $this.updateStatus("Getting data...", true);
            let data = await $this.getFiles();
            $this.updateStatus("Processing " + data.length + " files...", true);

            // remove files that are in the filebrowser but not in the json
            if (outer.querySelector("div.card")) {
                $this.updateStatus("Removing files...", true);
                let uuids = [];
                let file;
                for (file in data) {
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
                clone.querySelector(".title").innerHTML = data[file]["title"];
                clone.querySelector("img").src = data[file]["thumbnail_url"];
                clone.querySelector(".card-footer.file-info > i.filetype").className = data[file]["filetype_icon"];
                clone.querySelector(".card-footer.file-info > i.status").className = "status " + data[file]["status_icon"];
                clone.querySelector(".card-footer.file-info > span").innerHTML = data[file]["albums"].length;
                clone.dataset.bmaFileUuid=data[file]["uuid"];
                clone.dataset.bmaFileLastUpdate=data[file]["updated"];
                clone.dataset.bmaFileSize=data[file]["size_bytes"];
                clone.dataset.bmaFileType=data[file]["filetype"];
                deck.append(clone);
                // add this file to selectable
                $this.container._selectable.add(clone);
            };

            $this.container.querySelector("div.totals > .card-body").innerHTML = size + " bytes in " + data.length + " files.<br>" + counts["picture"] + " pictures, " + counts["video"] + " videos, " + counts["audio"] + " audios, " + counts["document"] + " documents.";
            $this.updateSummary();
            $this.updateStatus("Ready. Showing " + $this.container.querySelectorAll("div.file").length + " files.");
            // enable form
            $this.enableForm();
        };

        // update status function
        $this.updateStatus = function(message, busy) {
            if (busy) {
                $this.messages.innerHTML="<i class='fas fa-spinner fa-spin'></i> ";
            } else {
                $this.messages.innerHTML="<i class='fas fa-circle fa-beat-fade'></i> ";
            };
            $this.messages.innerHTML+=message;
        };

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

        $this.updateFileBrowser();
    };

    // init function
    async function bma_filebrowser_init() {
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
                    container._filebrowser = new BMAFileBrowser(body, messages, prefix);
                } else {
                    throw new Error("body or status element not found");
                };
            };
        };
    };
    window.bma_filebrowser_init = bma_filebrowser_init
})();

document.addEventListener("DOMContentLoaded", bma_filebrowser_init);
