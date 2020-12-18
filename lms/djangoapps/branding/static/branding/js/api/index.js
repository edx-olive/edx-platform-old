import _ from 'lodash';
import qs from 'qs';
import sigV4Client from "../helpers/sigV4Client";

export function ResponseError(message, body) {
    // message: message of the response exception
    // body: object (array) of the error.
    this.message = message
    this.body = body
    this.name = 'ResponseError'
}

export function raiseError(e) {
    const message = e.body || 'Oops! Something\'s getting wrong'
    throw new ResponseError(message, e.body)
}

export function checkStatus(response) {
    if (response.status >= 200 && response.status < 300) {
      return response.json().then(json => json, () => response)
    } else {
        let error
        if (response.status < 500 || response.status !== 404) {
            error = response.json()
        } else {
            error = response.text()
        }
        return error.then(e => {
            throw new ResponseError(response.statusText, e)
        })
    }
}

export const patchAWSSign = (url, awsSettings, params = {}) => {
    params = _.cloneDeep(params);

    const headers = params.headers;
    const body = params.data;
    const method = params.method || 'get';

    if (awsSettings.credentials.accessKeyId) {
        const parsedUrl = new URL(url);
        const path = parsedUrl.pathname;
        const queryParams = qs.parse(parsedUrl.search.substring(1));
        const config = {
            accessKey: awsSettings.credentials.accessKeyId,
            secretKey: awsSettings.credentials.secretAccessKey,
            sessionToken: awsSettings.credentials.sessionToken,
            region: awsSettings.region,
            endpoint: url,
        };
        const signedRequest = sigV4Client.newClient(config).signRequest({
            method,
            path,
            headers,
            queryParams,
            body,
        });
        params.headers = signedRequest.headers;
        url = signedRequest.url;
    } else {
        console.error("An error happened signing url " + url);
    }
    return { url, params };
}
