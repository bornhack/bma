// config (rendered serverside)
const uuid = "{{ uuid }}";
const host = "{{ host }}";
const count = "{{ count }}";

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

async function getFileMetadata(file_uuid) {
  const response = fetch("//" + host + "/api/v1/json/files/" + file_uuid + "/", {mode: 'cors'})
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
  const response = fetch("//" + host + "/api/v1/json/albums/" + album_uuid + "/", {mode: 'cors'})
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

