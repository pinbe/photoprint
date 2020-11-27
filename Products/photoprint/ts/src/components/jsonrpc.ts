export interface IJsonRpcRequest {
    jsonrpc: '2.0';
    method: string;
    params: any;
    id: number | string;
}

export interface JsonRpcResponse<Result> {
    request: IJsonRpcRequest;
    result?: Result;
    error?: {code: number, message: string, data?: any};
    id?: string;
}


export class JsonRpcRequest {

    url: string;

    constructor(url: string) {
        this.url = url;
    }

    send<Result>(method: string, params: any): Promise<JsonRpcResponse<Result>> {
        const jsonreq: IJsonRpcRequest = {
            jsonrpc: '2.0',
            method: method,
            params: params,
            id: new Date().valueOf()
        };
        return new Promise<JsonRpcResponse<Result>>(
            (resolve, reject) => {
                const req = new XMLHttpRequest();
                req.open('POST', this.url);
                req.addEventListener('load', (e) => {
                    const resp: XMLHttpRequest = <XMLHttpRequest>(e.target);
                    let jsonrpcresp: JsonRpcResponse<Result>;
                    if(resp.status === 200) {
                        try {
                            jsonrpcresp = JSON.parse(resp.responseText);
                            jsonrpcresp.request = jsonreq;
                        }
                        catch (e) {
                            reject({request: jsonreq,
                                error: {code: -32700, /* parse error */
                                        message: 'An error occurred on the client while parsing the JSON text',
                                        data: resp.responseText},
                                id: null});
                            return;
                        }

                        // Well formed jsonrpc response or error
                        if(jsonrpcresp.error) {
                            reject(jsonrpcresp);
                        }
                        else if (jsonrpcresp.result || jsonrpcresp.result === null) {
                            resolve(jsonrpcresp);
                        }
                    }

                    // http error => reject with a pseudo (not from server) json rpc error.
                    else {
                        reject({request: jsonreq,
                            error: {code: -32300 /* transport error */,
                                    message: `HTTP error: ${resp.status}`,
                                    data: resp.statusText},
                            id: null});
                    }

                });
                const fd = new FormData();
                fd.append('req', JSON.stringify(jsonreq));
                req.send(fd);
            }
        );
    }

}
