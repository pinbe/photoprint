import {JsonRpcRequest, JsonRpcResponse} from "./components/jsonrpc";

class CartEditForm {
    static readonly INPUT_TIMEOUT = 1000; // ms
    private form: HTMLFormElement;
    private portal_url: string;
    private timeoutId: number;

    constructor(form: HTMLFormElement, portal_url: string) {
        this.form = form;
        this.portal_url = portal_url;
        this.form.addEventListener('change', (e) => this.onFormChange(e));
        this.form.addEventListener('input', (e) => this.onInput(e));
    }

    private onFormChange(e: Event) {
        const target = <HTMLInputElement>e.target;
        if (!target.checkValidity())
            return;
        switch (target.name) {
            case 'quantity' :
                new JsonRpcRequest(`${this.portal_url}/cartrpc`)
                    .send<{unit_price: string, quantity: number, line_total: string}>(
                        'update_quantity',
                        {
                            quantity: parseInt(target.value, 10),
                            jobid: target.getAttribute('data-jobid')
                        }
                    ).then((resp) => {
                    console.log(resp.result);
                }, (resp: JsonRpcResponse<any>) => {
                    console.error(resp.error);
                });
                break;
        }

    }

    private onInput(e: Event) {
        if (this.timeoutId !== undefined)
            window.clearTimeout(this.timeoutId);
        this.timeoutId = window.setTimeout(() => this.onFormChange(e), CartEditForm.INPUT_TIMEOUT);
    }
}

window.addEventListener('load',
    () => new CartEditForm(<HTMLFormElement>document.getElementById('cart-form'),
        document.body.getAttribute('data-portal_url')))