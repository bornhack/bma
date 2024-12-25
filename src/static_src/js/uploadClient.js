/** Class UploadClient. this class is used for uploading files to the server and processing them. */
class UploadClient {
  /**
   * Create Upload Client instance.
   *
   * @param {string} client_id - oauth client_id
   * @param {function} callback - Done loading callback 
   */
  constructor(client_id, callback) {
    this.run = true;
    this.log = (log) => { console.log(log) }
    this.onFinished = (_active) => { }
    this.onDeQueue = (_job_count, _queue_count, _current, _total) => { }
    this.queue = []
    this.client_id = client_id
    this.client_uuid = ""
    this.oauth = new OauthClient(client_id, (token) => this.oauthReady(token));
    this.finished = [];
    this.allowedMimetypes = [];
    this.callback = callback;
    this.bma_version = JSON.parse(document.getElementById('bma_version').textContent);
    this.client_version = `js-client - BMA ${this.bma_version}`;
    this.activeJobs = 0;
    this.maxConcurrent = 2;
    this.skip_jobs = [];
    this.source_file_store = {};
    this.job_queue = [];
    this.running_jobs = 0;
    this.current_jobs = 0;
    this.total_jobs = 0;
    const cookie = this.getCookie("bma_uc_uuid");
    if (cookie) {
      this.client_uuid = cookie;
    } else {
      this.client_uuid = this.generateUUID();
      this.setCookie("bma_uc_uuid", this.client_uuid, 1);
    }
    this.updateProgress = (_item, _progress) => {};
  }

  /**
   * OAuth token callback
   *
   * @param {string} token - OAuth token
   */
  oauthReady(_token) {
    this.getClientConfig();
  }

  /**
   * Add a uploaded file
   *
   * @param {string} uuid - UUID of the uploaded file 
   * @param {string} source_url - URL of the source file
   * @param {object} file - File object
   */
  async addUploadedFile(uuid, source_url, file) {
    this.finished.push(uuid);
    const jobList = await this.assignJob({finished: false, file_uuid: uuid});
    this.storeSource(source_url, file);
    for (const job of jobList) {
      this.addToJobQueue(uuid, job);
    }
  }

  /**
   * Add job to job queue
   *
   * @param {string} uuid - UUID of basefile
   * @param {object} job - Job object
   */
  addToJobQueue(uuid, job) {
    if (!(job.source_url in this.source_file_store))
      throw new Error(`addToJobQueue: ${uuid} (${job.source_url}) not in sourcefiles`)
    this.current_jobs++;
    this.job_queue.push(
      {
        uuid: uuid,
        task:() => {
          return new Promise(resolve => resolve(
            this.executeJob(job)
          ))
        },
    });
  }

  /**
   * Add uploaded file to process queue 
   *
   * @param {string} uuid - UUID of the uploaded file 
   * @param {object} file - File object
   */
  addToQueue(uuid, file) {
    this.queue.push({uuid: uuid, file: file, tasks: []});
  }

  /**
   * Resize the picture keeping the AR
   *
   * @param {object} file - File 
   * @param {number} width - Width 
   * @param {number} height - Height 
   * @param {string} mimetype - MimeType
   * @returns {Promise} 
   */
  async resize(file, width, height, type = 'image/png') {
    return new Promise((resolve, reject) => {
      let quality = 0.6;
      if (type in this.config.encoding.images) {
        quality = this.config.encoding.images[type].quality / 100;
      }
      new Compressor(file, {
        quality: quality,
        maxWidth: width,
        maxHeight: height,
        mimeType: type,
        convertSize: -1,
        success(result) {
          resolve(result);
        },
        error(err) {
          console.log(err.message);
          reject(err);
        },                          
      });
    });
  }

  /**
   * Crop the picture to requested AR 
   *
   * @param {object} file - File 
   * @param {number} width - Width 
   * @param {number} height - Height 
   * @param {string} mimetype - MimeType
   * @returns {Promise} 
   */
  async crop(file, width, height, type = 'image/png') {
    return new Promise((resolve, reject) => {
      let quality = 0.6;
      if (type in this.config.encoding.images) {
        quality = this.config.encoding.images[type].quality / 100;
      }
      new Compressor(file, {
        quality: quality,
        width: width,
        height: height,
        mimeType: type,
        convertSize: -1,
        resize: 'cover',
        success(result) {
          resolve(result);
        },             
        error(err) {
          console.log(err.message);
          reject(err);
        },
      });
    });
  }

  /**
   * Exstract Exif information from image 
   *
   * @param {object} file - File 
   * @returns {Promise} 
   */
  async exif(file) {
    if ("dataURL" in file)
      return window.exifr.parse(file.dataURL)
    else
      console.log("Exif missing dataURL");
  }

  /**
   * Reformat exif data to schema used in BMA 
   *
   * @param {object} originalData - Original exif. 
   * @returns {object} Reformatted exif data. 
   */
  reformatExifData(originalData) {
    const formattedData = {
      Image: {},
      Thumbnail: {},
      EXIF: {},
    };

    // Map of property name changes if any
    const propertyMap = {
      "ISO": "ISOSpeedRatings",
      "ExposureCompensation": "ExposureBiasValue",
    };

    for (const key in originalData) {
      const value = originalData[key];
      const newKey = propertyMap[key] || key;

      if (typeof newKey === 'object') {
        newKey = newKey[value];
      }

      if (['ImageWidth', 'ImageHeight', 'Make', 'Model', 'Orientation', 'XResolution', 'YResolution', 'ResolutionUnit', 'Software', 'DateTime', 'YCbCrPositioning', 'ExifOffset'].includes(newKey)) {
        formattedData.Image[newKey] = value.toString();
      } else if ([].includes(newKey)) {
        formattedData.Thumbnail[newKey] = value.toString();
      } else {
        formattedData.EXIF[newKey] = value.toString();
      }
    }
    return formattedData;
  }

  /**
   * Execute a job item
   *
   * @param {object} job - Job information 
   * @returns {Promise} - The promise 
   */
  async executeJob(job) {
    if (!(job.source_url in this.source_file_store))
      throw new Error(`executeJob: ${job.basefile_uuid} not in sourcefiles`);
    if (this.source_file_store[job.source_url].type.startsWith("image/")) {
    switch(job.job_type) {
      case "ImageConversionJob":
      case "ThumbnailJob":
        const filename = `${job.job_uuid}.${job.filetype}`
        this.log(`Job for ${job.basefile_uuid}: ${job.job_type} ${job.width}x${job.height} ${job.mimetype} Custom aspect ratio: ${job.custom_aspect_ratio}`)
        if (job.custom_aspect_ratio)
          return this.crop(this.source_file_store[job.source_url], job.width, job.height, job.mimetype).then(img=> {
            this.uploadJobResult(job, img, filename, {"width": job.width, "height": job.height, "mimetype": job.mimetype})
          });
        else
          return this.resize(this.source_file_store[job.source_url], job.width, job.height, job.mimetype).then(img=> {
            this.uploadJobResult(job, img, filename, {"width": job.width, "height": job.height, "mimetype": job.mimetype})
          });
      /*
      case "ImageExifExtractionJob":
        this.log(`Job for ${job.basefile_uuid}: ${job.job_type} ${job.job_uuid}`)
        const exifOrg = await this.exif(this.source_file_store[job.source_url]);
        const exif = this.reformatExifData(exifOrg);
        const jsonFile = new Blob([JSON.stringify(exif)], { type: 'application/json' });
        console.log(exifOrg, exif);
        return this.uploadJobResult(job, jsonFile, "exif.json");
      */
      case "ThumbnailSourceJob":
        this.log(`Job for ${job.basefile_uuid}: ${job.job_type}`)
        return this.resize(this.source_file_store[job.source_url], 500, undefined, "image/webp").then(img=> {
          this.getImageDimensions(img).then((size) => {
            this.uploadJobResult(job, img, "thumbnail.webp", {"width": size.width, "height": size.height, "mimetype": "image/webp"})
          })
        });
      default:
        this.log(`Unsupported job type: ${job.job_type} ${job.job_uuid}`);
        this.skip_jobs.push(job.job_uuid);
        return this.unassignJob(job.job_uuid);
    }
    } else {
        this.log(`Unsupported filetype type: ${job.job_type} ${job.job_uuid} ${this.source_file_store[job.source_url].type}`);
        this.skip_jobs.push(job.job_uuid);
        return this.unassignJob(job.job_uuid);
    }
  }

  /**
   * Fetch file meta data from server 
   *
   * @param {object} job - Job entry 
   * @returns {Promise} 
   */
  async fetchFileMetadata(job) {
    try {
      const url = new URL(`${window.location.origin}/api/v1/json/files/${job.basefile_uuid}/`);
      const response = await fetch(url, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
        },
      });
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }

      const json = await response.json();
      return json.bma_response 
    } catch (error) {
      console.log(error.message);
      return [];
    }
  }

  /**
   * Fetch file
   *
   * @param {string} url - URL of the file to fetch 
   * @returns {Promise} 
   */
  async fetchFile(file_url) {
    try {
      const url = new URL(`${window.location.origin}${file_url}`)
      const result = await fetch(url, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
        },
      });
      const file = await result.blob();
      const contentType = result.headers.get('Content-Type');
      if (contentType === "image/webp") {
        return { url: file_url, file: new Blob([file], {type:"image/webp"})}
      }
      return { url: file_url, file: file }
    } catch (error) {
      console.log(error.message);
      return [];
    }
  }

  /**
   * Fetch the file list from server 
   *
   * @param {object} query - Query to execute 
   * @returns {Promise} 
   */
  async fetchFileList(query) {
    try {
      const url = new URL(`${window.location.origin}/api/v1/json/files/`);
      url.search = new URLSearchParams(query);
      const response = await fetch(url, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }

      const json = await response.json();
      return json.bma_response 
    } catch (error) {
      console.log(error.message);
      return [];
    }
  }

  /**
   * Fetch the joblist from server 
   *
   * @param {object} query - Query to execute 
   * @returns {Promise} 
   */
  async fetchJobList(query = {}) {
    try {
      const url = new URL(`${window.location.origin}/api/v1/json/jobs/`);
      if (this.skip_jobs.length > 0) {
        query["skip_jobs"] = this.skip_jobs.join(",");
      }
      url.search = new URLSearchParams(query);
      const response = await fetch(url, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }

      const json = await response.json();
      return json.bma_response 
    } catch (error) {
      console.log(error.message);
      return [];
    }
  }

  /**
   * Assign the job to this client 
   *
   * @param {object} query - Query to execute 
   * @returns {Promise} 
   */
  async assignJob(query = {finished: false, limit: 2}) {
    try {
      const url = new URL(`${window.location.origin}/api/v1/json/jobs/assign/`);
      if (this.skip_jobs.length > 0)
        query["skip_jobs"] = this.skip_jobs.join(",");
      url.search = new URLSearchParams(query);
      const response = await fetch(url, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
          "Content-Type": "application/json",
        },
        method: "POST",
        body: JSON.stringify({ "client_uuid": this.client_uuid, "client_version": this.client_version }),
      });
      if (response.status === 404)
        return [];
      if (!response.ok) {
        this.log(`Failed to assign jobs for ${JSON.stringify(query)}`);
        return false; 
      }
      const json = await response.json();
      return json.bma_response 
    } catch (error) {
      console.log(error.message);
      return [];
    }
  }

  /**
   * Unassign job 
   *
   * @param {string} uuid - UUID of job to unassign 
   * @returns {Promise} 
   */
  async unassignJob(uuid) {
    try {
      const url = new URL(`${window.location.origin}/api/v1/json/jobs/${uuid}/unassign/`)
      const response = await fetch(url, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
        },
        method: "POST",
      });
      const json = await response.json();
      return json.bma_response 
    } catch (error) {
      console.log(error.message);
      return [];
    }
  }

  /**
   * Upload the job results to the server 
   *
   * @param {object} item - Item to process 
   * @param {object} result - Result to upload. 
   * @param {string} filename - Name of the file 
   * @param {object} metadata - Metadata of the uploaded result 
   * @returns {array} bma_response 
   */
  async uploadJobResult(job, result, filename, metadata=undefined) {
    var data = new FormData()
    data.append('data', result, filename);
    data.append('client', JSON.stringify({ "client_uuid": this.client_uuid, "client_version": this.client_version }))
    if (metadata) {
      data.append('metadata', JSON.stringify(metadata))
    }

    try {
      const response = await fetch(`/api/v1/json/jobs/${job.job_uuid}/result/`, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
        },
        method: "POST",
        body: data,
      });
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }
      const json = await response.json();
      return json.bma_response 
    } catch (error) {
      console.log(error.message);
      return [];
    }
  }

  /**
   * Uploading ThumbnailSource images for thumbnails. 
   *
   * @param {string} uuid - UUID of file 
   * @param {object} result - Result to upload. 
   * @param {string} filename - Name of the file 
   * @param {object} metadata - Metadata of the uploaded result 
   * @returns {array} bma_response 
   */
  async uploadThumbnailSource(uuid, result, filename, metadata=undefined) {
    var data = new FormData()
    data.append('f', result, filename);
    data.append('client', JSON.stringify({ "client_uuid": this.client_uuid, "client_version": this.client_version }))
    if (metadata) {
      data.append('metadata', JSON.stringify(metadata))
    }

    try {
      const response = await fetch(`/api/v1/json/files/${uuid}/thumbnail/`, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
        },
        method: "POST",
        body: data,
      });
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }
      const json = await response.json();
      return json.bma_response 
    } catch (error) {
      console.log(error.message);
      return [];
    }
  }

  /**
   * Create a album from the items in the finished arrach 
   *
   * @param {string} name - Name of the album.
   * @param {string} description - Description of the album.
   * @param {array} files - List of file uuids to create a album with. 
   * @returns {array} bma_response 
   */
  async createAlbum(name, description, files = this.finished) {
    const data = {
      'title': name,
      'description': description,
      'files': files,
    }
    if (files.length === 0) return
    try {
      const response = await fetch(`/api/v1/json/albums/create/`, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
          "Content-Type": "application/json",
        },
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }
      this.finished = [];
      const json = await response.json();
      return json.bma_response 
    } catch (error) {
      console.log(error.message);
      return [];
    }
  }

  /**
   * Set a cookie 
   *
   * @param {string} cname - Name of the cookie 
   * @param {string} cvalue - Value of the cookie. 
   * @param {number} exdays - Days of validity.
   * @returns {string} Cookie contents 
   */
  setCookie(cname, cvalue, exdays) {
    const d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    let expires = "expires="+d.toUTCString();

    if (location.protocol === 'https:')
      document.cookie = cname + "=" + cvalue + ";Secure;SameSite=Strict;" + expires + ";path=/";
    else
      document.cookie = cname + "=" + cvalue + ";SameSite=Strict;" + expires + ";path=/";
  }

  /**
   * Get a cookie 
   *
   * @param {string} cname - Name of the cookie 
   * @returns {string} Cookie contents 
   */
  getCookie(cname) {
    let name = cname + "=";
    let ca = document.cookie.split(';');
    for(let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) == ' ') {
        c = c.substring(1);
      }
      if (c.indexOf(name) == 0) {
        return c.substring(name.length, c.length);
      }
    }
    return "";
  }

  /**
   * Generate UUID 
   *
   * @returns {string} UUID 
   */
  generateUUID() { // Public Domain/MIT
    var d = new Date().getTime();//Timestamp
    var d2 = ((typeof performance !== 'undefined') && performance.now && (performance.now()*1000)) || 0;//Time in microseconds since page-load or 0 if unsupported
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random() * 16;//random number between 0 and 16
      if(d > 0){//Use timestamp until depleted
        r = (d + r)%16 | 0;
        d = Math.floor(d/16);
      } else {//Use microseconds since page-load if supported
        r = (d2 + r)%16 | 0;
        d2 = Math.floor(d2/16);
      }
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }

  /**
   * Extract keys from object 
   *
   * @param {object} obj - Object
   * @returns {array} Keys
   */
  extractKeys(obj) {
    const keys = [];
    for (const key in obj) {
      if (typeof obj[key] === 'object') {
        keys.push(...this.extractKeys(obj[key]));
      } else {
        keys.push(key);
      }
    }
    return keys;
  }

  /**
   * Get client configuration from server.
   *
   */
  async getClientConfig() {
    try {
      const response = await fetch(`/api/v1/json/jobs/settings/`, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
        },
      });
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }
      this.finished = [];
      const json = await response.json();
      this.config = json.bma_response;
      this.allowedMimetypes = this.extractKeys(this.config.filetypes)
      this.callback();
    } catch (error) {
      console.log(error.message);
    }
  }

  /**
   * Extract width and height from image blob.
   *
   * @param {Blob} blob - Image blob
   * @returns {Promise} - width and height
   */
  getImageDimensions(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = function(event) {
        const img = new Image();
        img.onload = function() {
          resolve({ width: img.width, height: img.height});
        };
        img.onerror = reject;
        img.src = event.target.result;
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * Get a list of unique items from array of objects
   * @param {array} objects - Array of Objects
   * @param {string} key - Key to get uniques from
   * @returns {set} - List of unique items
   */
  getUnique(objects, key) {
    const uniqueUuids = new Set();
    objects.forEach(obj => {
      uniqueUuids.add(obj[key]);
    });
    return [...uniqueUuids];
  }

  /**
   * Store a source file
   *
   * @param {string} uuid - UUID of the file
   * @param {blob} file - Blob of the source file
   */
  storeSource(url, file) {
    this.source_file_store[url] = file;
  }

  /**
   * Get a source file
   *
   * @param {blob} file - Blob of the source file
   * @param {string} uuid - UUID of the file
   */
  getSource(url) {
    return this.source_file_store[url];
  }

  /**
   * Start the next grind job.
   */
  async processNextJob() {
    if (this.running_jobs < this.maxConcurrent && this.job_queue.length > 0 && this.run) {
      const job = this.job_queue.shift()
      this.running_jobs++
      this.onDeQueue(this.running_jobs, this.job_queue.length, this.current_jobs, this.total_jobs);
      job.task()
        .then(() => {
          this.running_jobs--;
          this.processNextJob();
        })
        .catch(error => {
          this.running_jobs--;
          console.error('Error processing task:', error);
          this.processNextJob();
        });
    } else if (this.job_queue.length === 0 && this.run) {
      this.total_jobs = this.total_jobs + this.current_jobs;
      this.current_jobs = 0;
      this.onFinished(this.running_jobs);
    }
  }

  /**
   * Start Grinder Threads.
   */
  startGrinder() {
    const conCount = this.maxConcurrent - this.running_jobs;
    this.run = true;
    for (var i = 0; i < conCount; i +=1){
      this.processNextJob();
    }
  }

  /**
   * Fetch new work from backend and start grinding
   */
  fetchNewWork() {
    let downloadJobs = [];
    this.fetchJobList({client_uuid: this.client_uuid, finished: false}).then((jobs) => {
      for (const file of this.getUnique(jobs, "source_url")) {
        if (!(file in this.source_file_store))
          downloadJobs.push(this.fetchFile(file));
      }
      Promise.all(downloadJobs).then((imgs)=> {
        for (const img of imgs) {
          this.storeSource(img.url, img.file);
        }
        for (const job of jobs) {
          this.addToJobQueue(job.basefile_uuid, job);
        }
        this.startGrinder();
      })
    });
  }
}
