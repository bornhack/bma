// config (rendered serverside)
const uuid = "{{ uuid }}";
const host = "{{ host }}";
const count = "{{ count }}";
const width = {{ width }};
const ratio = "{{ ratio }}";
const height = {{ height }};

const templateFiles = "{{ files|escapejs }}";

// custom error class
class BmaNotFoundError extends Error {
  constructor(message) {
    super(message);
    this.name = "BmaNotFoundError";
  }
}
class BmaApiError extends Error {
  constructor(message) {
    super(message);
    this.name = "BmaApiError";
  }
}
class BmaPermissionError extends Error {
  constructor(message) {
    super(message);
    this.name = "BmaPermissionError";
  }
}

const main_loader = document.createElement('div');
main_loader.id = "photoswipe-" + count + "-loader"
main_loader.innerHTML = `<div class="spinner-grow" role="status"></div><span class="h3">Loading Gallery....</span>`;
// A reference to the currently running script
const bma_script = document.scripts[document.scripts.length - 1];
bma_script.parentElement.insertBefore(main_loader, bma_script);


async function getFileMetadata(file_uuid) {
  const response = fetch(host + "/api/v1/json/files/" + file_uuid + "/", {mode: 'cors'})
    .then((x) => {
      if (!x.ok) {
        // handle non-2xx x code
        if (x.status === 404) {
          throw new BmaNotFoundError("File UUID " + file_uuid + " not found!");
        } else if (x.status === 403) {
          throw new BmaPermissionError("No permission for file UUID " + file_uuid + "!");
        } else {
          throw new BmaApiError("BMA API returned unexpected x code " + x.status);
        }
      }
      return x.json()
    })
    .then((x) => ({[file_uuid]: x['bma_response']}))
    .catch((response) => {
      console.log(response);
    });
  return response
}

async function getAlbumMetadata(album_uuid) {
  const response = fetch(host + "/api/v1/json/albums/" + album_uuid + "/", {mode: 'cors'})
    .then((response) => {
      if (!response.ok) {
        // handle non-2xx response code
        if (response.status === 404) {
          throw new BmaNotFoundError("Album UUID " + album_uuid + " not found!");
        } else if (response.status === 403) {
          throw new BmaPermissionError("No permission for album UUID " + album_uuid + "!");
        } else {
          throw new BmaApiError("BMA API returned unexpected response code " + response.status);
        }
      }
      return response.json();
    })
    .then((data) => data["bma_response"])
    .catch((response) => {
      console.log(response);
    });
  return response;
}

