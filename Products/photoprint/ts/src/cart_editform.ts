import {JsonRpcRequest, JsonRpcResponse} from "./components/jsonrpc";

type Line = [string, number, string];

interface Totals {
    lines_total: string;
    tax: string;
}

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
                    .send<{ lines: Line[], totals: Totals }>(
                        'update_quantity',
                        {
                            quantity: parseInt(target.value, 10),
                            jobid: target.getAttribute('data-jobid')
                        }
                    ).then((resp) => {
                    this.updateLines(resp.result.lines);
                    this.updateTotals(resp.result.totals);
                    target.size = Math.max(target.value.length, 2);
                }, (resp: JsonRpcResponse<unknown>) => {
                    console.log(resp.error.data);
                    target.value = resp.error.data.quantity;
                });
                break;
        }

    }

    private onInput(e: Event) {
        if (this.timeoutId !== undefined)
            window.clearTimeout(this.timeoutId);
        this.timeoutId = window.setTimeout(() => this.onFormChange(e), CartEditForm.INPUT_TIMEOUT);
    }


    private updateLines(lines: Line[]) {
        const tbody = <HTMLTableSectionElement>this.form.querySelector('.cart_content');
        const rows = tbody.getElementsByTagName('tr');
        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const cells = row.getElementsByTagName('td');
            cells[4].innerHTML = lines[i][0]; // unit price
            cells[5].getElementsByTagName('input')[0].value = (new Number(lines[i][1])).toString(); // quantity
            cells[6].innerHTML = lines[i][2]; // line total
        }
    }

    private updateTotals(totals: Totals) {
        this.form.querySelector('.total').querySelector('.lines_total')
            .innerHTML = totals.lines_total;
        this.form.querySelector('.total').querySelector('.tax')
            .innerHTML = totals.tax;
    }
}

window.addEventListener('load',
    () => new CartEditForm(<HTMLFormElement>document.getElementById('cart-form'),
        document.body.getAttribute('data-portal_url')))