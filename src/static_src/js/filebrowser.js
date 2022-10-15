// getting some closure
(async function() {
    function BMAFileBrowser(container, messages) {
        // this ensures a clean object even if the new keyword is forgotten
        if (!(this instanceof BMAFileBrowser))  return new BMAFileBrowser(container, messages);

        // make $this always refer to this instance of BMAFileBrowser
        let $this = this;
        $this.container = container;
        $this.messages = messages;

        // the file template
        let template = document.createElement('template');
        template.innerHTML = `
<div class="card file">
  <span class="position-absolute top-0 end-0 p-1 bg-success border border-light selected-icon"><i class="fas fa-check"></i></span>
  <img class="card-img-top">
  <div class="file-status-icon"></div>
  <div class="file-title card-body p-1"><i></i> <span class="small title"></span></div>
  <div class="file-info card-footer p-1 d-inline-flex align-items-center justify-content-evenly">
    <i class="status"></i>
    <span class="badge text-bg-dark"></span>
  </div>
</div>`;

        // getfiles function
        $this.getFiles = async function() {
            // start building url
            let url = new URL(window.location.protocol + "//" + window.location.host + "/api/v1/json/files/");

            // get filetypes element
            let el = $this.container.querySelector("select[name='filetype']");
            if (el.selectedOptions.length) {
                // filter by filetype
                const filetypes = Array.from(el.selectedOptions).map(v=>v.value);
                for (t of filetypes) {
                    url.searchParams.append("filetypes", t);
                };
            };

            // get filestatus element
            el = $this.container.querySelector("select[name='filestatus']");
            if (el.selectedOptions.length) {
                // filter by file status
                const statuses = Array.from(el.selectedOptions).map(v=>v.value);
                for (s of statuses) {
                    url.searchParams.append("statuses", s);
                };
            };

            // get search element
            el = $this.container.querySelector("input[name='search']");
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
                for (button of buttons) {
                    button.removeAttribute("disabled");
                };
            } else {
                $this.container.querySelector("div.selection > .card-body").innerHTML = "0 bytes in 0 files<br>0 pictures, 0 videos, 0 audios, 0 documents.";
                let buttons = $this.container.querySelectorAll("div.btn-group.actions > button");
                for (button of buttons) {
                    button.setAttribute("disabled", "");
                };
            };

        };

        // createFileBrowser function
        $this.createFileBrowser = async function() {
            // create outer div
            let outer = document.createElement("div");
            outer.classList.add("filebrowser-container");

            // create toolbar and buttongroup
            let toolbar = document.createElement("div");
            toolbar.classList.add("btn-toolbar");
            toolbar.innerHTML = `
<div class="container-fluid">
<nav class="navbar bg-light p-2 pe-0 border">

<div class="form-group me-2 h-25 border p-2">
  <form class="row gy-2 gx-3 align-items-center">
  <div class="col-auto">
    <select name="filetype" class="form-select" multiple>
      <option value="Picture">Picture</option>
      <option value="Video">Video</option>
      <option value="Audio">Audio</option>
      <option value="Document">Document</option>
    </select>
 </div>
  <div class="col-auto">
    <select name="filestatus" class="form-select" multiple>
      <option value="PENDING_MODERATION">Pending moderation</option>
      <option value="UNPUBLISHED">Unpublished</option>
      <option value="PUBLISHED">Published</option>
      <option value="PENDING_DELETION">Pending deletion</option>
    </select>
  </div>
  <div class="col-auto">
    <input type="text" name="search" placeholder="search..."></input>
  </div>
  <div class="col-auto">
    <button name="filter" type="button" class="btn btn-secondary"><i class='fa-solid fa-update'></i> Filter</button>
  </div>
</div>

<div class="card border me-2 totals">
  <div class="card-header">Totals</div>
  <div class="card-body">0 bytes in 0 files<br>0 pictures, 0 videos, 0 audios, 0 documents.</div>
</div>

<div class="card border me-2 selection">
  <div class="card-header">Selection
  <div class="btn-group me-2 actions float-end">
    <button type="button" class="btn btn-success" disabled><i class='fa-solid fa-cloud-arrow-up'></i></button>
    <button type="button" class="btn btn-danger" disabled><i class='fa-solid fa-cloud-arrow-down'></i></button>
    <button type="button" class="btn btn-primary" disabled><i class='fa-solid fa-plus'></i></button>
  </div>
</div>
<div class="card-body">0 bytes in 0 files<br>0 pictures, 0 videos, 0 audios, 0 documents.</div>
</div>
</nav>
</div>`
            outer.append(toolbar);

            let deck = document.createElement("div");
            deck.classList.add("file-container");
            deck.classList.add("d-flex");
            deck.classList.add("align-content-start");
            deck.classList.add("flex-wrap");
            outer.append(deck);

            // ok, add to the container
            $this.container.append(outer);
            $this.container.querySelector("button[name='filter']").addEventListener("click", $this.updateFileBrowser);
        };

        $this.log = function(message) {
            console.log($this.container.id + ": " + message);
        };

        // updateFileBrowser function
        $this.updateFileBrowser = async function() {
            // get or initiate filebrowser as needed
            let outer;
            outer = $this.container.querySelector(".filebrowser-container");
            if (!outer) {
                $this.createFileBrowser();
                outer = $this.container.querySelector(".filebrowser-container");
            };

            // get files from server
            $this.updateStatus("Getting data...", true);
            let data = await $this.getFiles();
            $this.updateStatus("Processing " + data.length + " files...", true);

            // remove files that are in the filebrowser but not in the json
            if (outer.querySelector("div.card")) {
                $this.updateStatus("Removing files...", true);
                let uuids = [];
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
            for (file in data) {
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
                let clone = template.content.cloneNode(true).querySelector("div");
                clone.querySelector(".title").innerHTML = data[file]["title"];
                clone.querySelector("img").src = data[file]["url"];
                clone.querySelector(".card-body.file-title > i").classList.add(...data[file]["filetype_icon"].split(" "));
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
            for (const container of containers) {
                let body = document.getElementById(container.dataset.body);
                let messages = document.getElementById(container.dataset.messages);
                if ( body && messages ) {
                    new BMAFileBrowser(body, messages);
                } else {
                    throw new Error("body or status element not found");
                };
            };
        };
    };
    window.bma_filebrowser_init = bma_filebrowser_init
})();

document.addEventListener("DOMContentLoaded", bma_filebrowser_init);
