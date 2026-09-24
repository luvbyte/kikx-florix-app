const trixApi = {
  baseUrl: window.location.origin + "/_api",

  headers: {
    Accept: "application/json"
  },

  // Configure API
  configure(options = {}) {
    const { baseUrl, headers = {} } = options;

    if (baseUrl !== undefined) {
      this.baseUrl = baseUrl;
    }

    this.headers = {
      ...this.headers,
      ...headers
    };

    return this;
  },

  // Build URL
  buildUrl(url) {
    if (/^https?:\/\//i.test(url)) {
      return url;
    }

    return `${this.baseUrl}${url}`;
  },

  // Handle response
  async handleResponse(response) {
    const contentType = response.headers.get("content-type") || "";

    const data = contentType.includes("application/json")
      ? await response.json()
      : await response.text();

    if (!response.ok) {
      throw {
        status: response.status,
        statusText: response.statusText,
        data
      };
    }

    return data;
  },

  // GET request
  async fetch(url, options = {}) {
    const { params, headers = {}, ...fetchOptions } = options;

    let finalUrl = this.buildUrl(url);

    if (params) {
      const searchParams = new URLSearchParams();

      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value);
        }
      });

      const query = searchParams.toString();

      if (query) {
        finalUrl += `${finalUrl.includes("?") ? "&" : "?"}${query}`;
      }
    }

    const response = await window.fetch(finalUrl, {
      method: "GET",
      ...fetchOptions,
      headers: {
        ...this.headers,
        ...headers
      }
    });

    return this.handleResponse(response);
  },

  // POST request with params
  async submit(url, params = {}, options = {}) {
    const { headers = {}, ...fetchOptions } = options;

    const isFormData = params instanceof FormData;

    const response = await window.fetch(this.buildUrl(url), {
      method: "POST",
      ...fetchOptions,
      headers: {
        ...this.headers,
        ...(isFormData
          ? {}
          : {
              "Content-Type": "application/json"
            }),
        ...headers
      },
      body: isFormData ? params : JSON.stringify(params)
    });

    return this.handleResponse(response);
  },

  // POST any type of data
  async submitPost(url, body, options = {}) {
    const { headers = {}, ...fetchOptions } = options;

    let requestBody = body;
    let contentType = {};

    if (
      body !== null &&
      typeof body === "object" &&
      !(body instanceof FormData) &&
      !(body instanceof Blob) &&
      !(body instanceof ArrayBuffer)
    ) {
      requestBody = JSON.stringify(body);

      contentType = {
        "Content-Type": "application/json"
      };
    }

    const response = await window.fetch(this.buildUrl(url), {
      method: "POST",
      ...fetchOptions,
      headers: {
        ...this.headers,
        ...contentType,
        ...headers
      },
      body: requestBody
    });

    return this.handleResponse(response);
  },

  // Upload multiple files with progress
  upload(url, files, options = {}) {
    return new Promise((resolve, reject) => {
      const {
        fieldName = "files",
        data = {},
        headers = {},
        onProgress,
        ...xhrOptions
      } = options;

      const formData = new FormData();

      // Append additional data
      Object.entries(data).forEach(([key, value]) => {
        formData.append(key, value);
      });

      // Append multiple files
      const fileList = Array.isArray(files) ? files : Array.from(files);

      fileList.forEach(file => {
        formData.append(fieldName, file);
      });

      const xhr = new XMLHttpRequest();

      xhr.open("POST", this.buildUrl(url), true);

      // Headers
      Object.entries({
        ...this.headers,
        ...headers
      }).forEach(([key, value]) => {
        xhr.setRequestHeader(key, value);
      });

      // Upload progress
      xhr.upload.addEventListener("progress", event => {
        if (!event.lengthComputable) {
          return;
        }

        const percent = Math.round((event.loaded / event.total) * 100);

        if (typeof onProgress === "function") {
          onProgress({
            percent,
            loaded: event.loaded,
            total: event.total
          });
        }
      });

      // Request completed
      xhr.addEventListener("load", () => {
        const contentType = xhr.getResponseHeader("content-type") || "";

        let responseData = xhr.responseText;

        if (contentType.includes("application/json")) {
          try {
            responseData = JSON.parse(xhr.responseText);
          } catch {
            responseData = xhr.responseText;
          }
        }

        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(responseData);
        } else {
          reject({
            status: xhr.status,
            statusText: xhr.statusText,
            data: responseData
          });
        }
      });

      // Network error
      xhr.addEventListener("error", () => {
        reject({
          message: "Network error"
        });
      });

      // Request aborted
      xhr.addEventListener("abort", () => {
        reject({
          message: "Upload aborted"
        });
      });

      // Timeout
      if (xhrOptions.timeout) {
        xhr.timeout = xhrOptions.timeout;

        xhr.addEventListener("timeout", () => {
          reject({
            message: "Upload timeout"
          });
        });
      }

      xhr.send(formData);
    });
  }
};
