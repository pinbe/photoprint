import {JsonRpcRequest, JsonRpcResponse} from "./components/jsonrpc";
import * as d3 from "d3";
import * as $ from "jquery";
import "bootstrap";
import "./custom.scss";
import i18next, {TOptions} from "i18next";
import HttpApi from "i18next-http-backend";
import LanguageDetector from "i18next-browser-languagedetector";

const _ = (s: string, options?: TOptions): string => i18next.t(s, options);

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
        this.form.addEventListener('click', (e) => this.onClick(e));
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

    private onClick(e: Event) {
        let target: HTMLElement = <HTMLElement>e.target;
        while (target !== this.form) {
            target = target.parentElement;
            if (target.tagName === 'A')
                break;
        }
        if (target.classList.contains('btn') &&
            target.classList.contains('del')) {
            e.preventDefault();
            target.blur();
            const self = this;

            let modal = d3.select(document.body)
                .append('div')
                .attr('class', 'modal fade')
                .attr('tabindex', '-1')
            ;
            modal.html(`
                <div class="modal-dialog modal-dialog-centered"
                     role="document">
                  <div class="modal-content">
                    <div class="modal-body">
                      <h5 style="text-align: center">${_('Confirm deletion?')}</h5>
                    </div>
                    <div class="modal-footer">
                      <div style="display: flex;
                                  justify-content: space-between;
                                  width: 100%">
                        <button type="button"
                                class="btn btn-secondary"
                                data-dismiss="modal">${_('Cancel')}</button>
                        <button type="button"
                                class="btn btn-primary"
                                name="confirm">${_('Confirm')}</button>
                      </div>
                    </div>
                  </div>
                </div>
            `);
            $(modal.node())
                .modal('show')
                .on('hidden.bs.modal', () => modal.remove())
            ;
            modal.select('button[name="confirm"]')
                .on('click', () => {
                    const jobid =
                        (<HTMLInputElement>d3.select(target.parentElement)
                            .select('input[name="quantity"]')
                            .node())
                            .getAttribute('data-jobid');

                    new JsonRpcRequest(`${this.portal_url}/cartrpc`)
                        .send<{ lines: Line[], totals: Totals }>(
                            'delete_job',
                            {jobid: jobid}
                        ).then((resp) => {
                        while (target.tagName !== 'TR') {
                            target = target.parentElement;
                        }
                        d3.select(target).remove();
                        if (resp.result.lines.length === 0) {
                            window.location.href = self.portal_url + '/my_cart';
                            return;
                        }
                        self.updateLines(resp.result.lines);
                        self.updateTotals(resp.result.totals);
                        $(modal.node())
                            .modal('hide');
                    }, (resp: JsonRpcResponse<unknown>) => {
                        console.error(resp.error.data);
                        $(modal.node())
                            .modal('hide');
                    });

                })
            ;

        }
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

function main() {
    const portal_url = document.body.getAttribute('data-portal_url');

    i18next
        .use(HttpApi)
        .use(LanguageDetector)
        .init({
            cleanCode: true,
            ns: ['photoprint',],
            defaultNS: 'photoprint',
            nsSeparator: false,
            keySeparator: false,
            backend: {
                loadPath: portal_url + '/photoprint/jsbuild/locales/{{lng}}/{{ns}}.json',
            },
            detection: {
                order: [
                    'navigator',
                    'querystring',
                    'cookie',
                    'localStorage',
                    'sessionStorage',
                    'navigator',
                    'htmlTag',
                    'path',
                    'subdomain'
                ],
            },
        })
        .then(() => {
            new CartEditForm(
                <HTMLFormElement>document.getElementById('cart-form'),
                portal_url)
        });

}

$(() => main());
