/** Class OAuth client lib - Used for getting oauth tokens from the api */
class OauthClient {
  /**
   * Create OAuth Client instance.
   *
   * @param {string} client_id - oauth client_id
   * @param {function} callback - Has token callback 
   */
  constructor(client_id, callback) {
    this.token = undefined;
    this.alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    this.callback = callback;
    this.getToken(client_id);
  }

  /**
   * Get a random number.
   *
   * @param {number} max - Max number
   * @return {number} Random number
   */
  randomInt(max) {
    return Math.floor(Math.random() * max)
  }

  /**
   * Generate oAuthChallenge from Verifier
   *
   * @param {string} codeVerifier - Verifier code 
   * @return {string} Base64 Challenge 
   */
  async oauthGetChallenge(codeVerifier) {
    const digest = await crypto.subtle.digest("SHA-256",
      new TextEncoder().encode(codeVerifier));

    return btoa(String.fromCharCode(...new Uint8Array(digest)))
      .replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
  }

  /**
   * Get Base64 oAuth Verifier
   *
   * @return {string} Base64 Verifier 
   */
  oauthGetVerifier() {
    // Generate a random code verifier
    const codeVerifierLength = 43 + this.randomInt(52);
    const codeVerifier = Array.from({ length: codeVerifierLength }, () => this.alphabet[this.randomInt(this.alphabet.length)]).join('');

    // Encode the code verifier in base64
    return Base64.encode(codeVerifier); 
  }

  /**
   * Make the random state data
   *
   * @return {string} State value 
   */
  oauthGetState() {
    // Generate a random state
    const stateLength = 15;
    return Array.from({ length: stateLength }, () => this.alphabet[this.randomInt(this.alphabet.length)]).join('');
  }

  /**
   * Send authorization request to the API.
   *
   * @param {string} csrf - CSRF Token
   * @param {string} client_id - OAuth client_id
   * @param {string} codeChallengeBase64 - Base64 encoded Challenge
   * @param {string} state - State value 
   * @return {array} [rescode, resstate] 
   */
  async sendAuthorizationRequest(csrf, client_id, codeChallengeBase64, state) {
    const requestData = new URLSearchParams();
    requestData.append('csrfmiddlewaretoken', csrf);
    requestData.append('client_id', client_id);
    requestData.append('state', state);
    //Using this url just to get a 200 on the redirect
    requestData.append('redirect_uri', window.location.origin + "/api/csrf/");
    requestData.append('response_type', 'code');
    requestData.append('code_challenge', codeChallengeBase64);
    requestData.append('code_challenge_method', 'S256');
    requestData.append('scope', 'read');
    requestData.append('allow', 'Authorize');
    requestData.append('claims', '');
    requestData.append('nonce', '');
    try {
      const response = await fetch("/o/authorize/", {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrf,
        },
        body: requestData
      }).catch((error) => {
        console.log(error)
      });
      const urlParams = new URLSearchParams(response.url.split("?")[1]);
      const resstate = urlParams.get('state');
      const rescode = urlParams.get('code');
      return [rescode, resstate] 
    } catch (error) {
      console.error('Error:', error);
    }
  }

  /**
   * Send token request to the API.
   *
   * @param {string} authcode - OAuth Auth code 
   * @param {string} client_id - OAuth client_id
   * @param {string} code_verifier - Base64 encoded verifier 
   * @return {promise<object>} Token response
   */
  async sendTokenRequest(authcode, client_id, code_verifier) {
    const requestData = new URLSearchParams();
    requestData.append("grant_type", "authorization_code");
    requestData.append("code", authcode);
    //Using this url just to get a 200 on the redirect
    requestData.append('redirect_uri', window.location.origin + "/api/csrf/");
    requestData.append("client_id", client_id);
    requestData.append("code_verifier", code_verifier);
    try {
      const response = await fetch("/o/token/", {
        method: 'POST',
        body: requestData
      });
      if (!response.ok) {
        throw new Error('Request failed');
      }
      return await response.json();
    } catch (error) {
      console.error('Error:', error);
    }
  }

  /**
   * Get token 
   *
   * @param {string} client_id - OAuth client_id
   * @return {string} Token
   */
  async getToken(client_id) {
    const verifier = this.oauthGetVerifier();
    const state = this.oauthGetState();
    const challenge = await this.oauthGetChallenge(verifier)
    const csrf = JSON.parse(document.body.getAttribute("hx-headers"))["x-csrftoken"];
    const auth = await this.sendAuthorizationRequest(csrf, client_id, challenge, state)
    if (auth[1] == state) {
      const token = await this.sendTokenRequest(auth[0], client_id, verifier);
      this.fullToken = token;
      this.token = token.access_token;
      if (this.callback) this.callback(this.token);
      return this.token;
    }
  }
}
