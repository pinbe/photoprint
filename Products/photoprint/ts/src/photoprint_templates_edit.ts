import * as d3 from "d3";
import i18next, {TOptions} from "i18next";
import HttpApi from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector'

const _ = (s: string, options?: TOptions): string => i18next.t(s, options);
const TR_DURATION = 500; // ms

type Sel = d3.Selection<HTMLElement, any, HTMLElement, any>;
type I18NString = { [lang: string]: string };
type PriceRange = {
    start: number,
    stop: number,
    price: number
};
type Format = {
    reference: string,
    label: I18NString,
    short_edge: number,
    long_edge: number,
    copies: number,
    price: number,
    prices_ranges: PriceRange[],
    finishes: string[],
};

type PrintInfos = {
    formats: Format[]
};

class PrintOptionsEditor {
    private absUrl: string;
    private formatsWrapper: HTMLTableDataCellElement;

    constructor(absUrl: string) {
        this.absUrl = absUrl;
        let cells = document.querySelectorAll<HTMLTableDataCellElement>('#print_options_editor > tr > td');
        this.formatsWrapper = cells[0];
        d3.select(this.formatsWrapper)
            .append('div')
            .attr('class', 'formats')
        ;
        d3.select(this.formatsWrapper)
            .append('div')
            .attr('class', 'buttons')
            .append('a')
            .on('click', () => this.createFormat())
            .attr('href', '#')
            .attr('title', _("Add new format…"))
            .append('i')
            .attr('class', 'fas fa-plus')
        ;

        d3.json(`${this.absUrl}/printingOptions/printoffer/json`)
            .then((infos: PrintInfos) => {
                this.updateFormats(infos.formats);
            })
    }

    private updateFormats(formats: Array<Format>, editLast=false) {
        const formatUpdate = d3.select(this.formatsWrapper).select('div.formats').selectAll('div')
            .data(formats);
        const formatEnter = formatUpdate.enter().append('div')
        const formatExit = formatUpdate.exit().remove();

        formatEnter.merge(formatUpdate)
            .html((d:Format, i: number) => PrintOptionsEditor.formatViewHtml(d, i))
            .on('click', (d: Format, i: number, g: Array<HTMLDivElement>) => {
                this.onFormatClick(d, i, g);
            })
        ;
        if(editLast) {
            const editbtn: HTMLElement =
                <HTMLElement>
                d3.select(this.formatsWrapper).select('div.formats > div:last-child i.btn.edit').node();
            editbtn.dispatchEvent(new MouseEvent('click', {view: window, bubbles:true, cancelable: true}));
            d3.select(this.formatsWrapper).select('div.formats > div:last-child input')
                .call((s) => (<HTMLInputElement>s.node()).focus())
            ;
        }
    }

    private createFormat() {
        d3.event.stopPropagation();
        d3.event.preventDefault();

        let params: FormData = new FormData();
        params.append('name', 'format');
        params.append('indent:int', '2');
        let url = `${this.absUrl}/printingOptions/printoffer/getTemplate`;
        d3.json(
            url,
            {
                body: params,
                method: 'POST'
            }
        ).then((format: Format) => {
            let data = d3.select(this.formatsWrapper).select('div.formats')
                .selectAll('div').data();
            data.push(format);
            this.updateFormats(<Format[]>data, true);
        });
    }

    private static formatViewHtml(fmt: Format, index: number): string {
        let lbl = '';
        for (let [lang, value] of Object.entries(fmt.label)) {
            lbl += `<li>${value}@${lang}</li>`
        }
        let prices_ranges = '';
        for (let range of fmt.prices_ranges) {
            prices_ranges += `<li>[${range.start}, ${range.stop}] ${range.price}</li>`;
        }
        return `
                <table class="TwoColumnForm">
                  <tr>
                    <td colspan="2" style="text-align: right">
                      <a href="#" title="${_("Edit")}">
                        <i class="btn edit fas"></i>
                      </a>
                      <a href="#" title="${_("Delete")}">
                        <i class="btn delete fas fa-backspace"></i>
                      </a>
                    </td>
                  </tr>
                  <tr>
                    <th>${_("Reference")}</th>
                    <td>
                      <span data-name="reference" data-pattern=".+">${fmt.reference}</span>
                    </td>
                  </tr>
                  <tr>
                    <th>${_("Label")}</th>
                    <td>
                      <ul data-name="label" data-line_pattern="(.*)(@)(\\w\\w)$">${lbl}</ul>
                    </td>
                  </tr>
                  <tr>
                    <th>${_("Short edge")}</th>
                    <td>
                      <span data-name="short_edge" data-pattern="^\\d+$">${fmt.short_edge}</span> cm
                    </td>
                  </tr>
                  <tr>
                    <th>${_("Long edge")}</th>
                    <td>
                      <span data-name="long_edge" data-pattern="^\\d+$">${fmt.long_edge}</span> cm
                    </td>
                  </tr>
                  <tr>
                    <th>${_("Price")}</th>
                    <td>
                      <span data-name="price" data-pattern="^\\d+$">${fmt.price}</span> ${_("€ ET")}
                    </td>
                  </tr>
                  <tr>
                    <th>${_("Scarcity")}</th>
                    <td>
                      <ul data-name="prices_ranges"
                          data-line_pattern="^\\s*$|^\\s*(\\[)\\s*(\\d+)\\s*(,\\s*)(\\d+)\\s*(\\])(\\s*)(\\d+)\\s*$">${prices_ranges}</ul>
                    </td>
                  </tr>
                  <tr>
                    <th>${_("Copies")}</th>
                    <td>
                      <span data-name="copies" data-pattern="^\\d+$">${fmt.copies}</span>
                    </td>
                  </tr>
                </table>
                `;
    }

    private onFormatClick(fmt: Format, i: number, g: HTMLDivElement[]) {
        const evt = d3.event;
        const target = evt.target;
        if (target.classList.contains('btn')) {
            evt.stopPropagation();
            evt.preventDefault();
            if(target.classList.contains('edit')) {
                target.classList.remove('edit');
                target.classList.add('validate');
                target.parentElement.setAttribute('title', _("Save"));
                this.startEdit(fmt, i, g);
            }
            else if (target.classList.contains('delete'))
                this.deleteFormat(fmt, i, g);
            else if (target.classList.contains('validate'))
                this.saveFormat(fmt, i, g);
        }
    }

    private startEdit(fmt: Format, i: number, g: HTMLDivElement[]) {
        d3.select(g[i]).selectAll('*[data-name]')
            .each((d, i, g)=> {
                const elt = <HTMLElement>g[i];
                const name = (elt.getAttribute('data-name'));
                const parent = elt.parentElement;
                let input: HTMLElement;
                switch (elt.tagName) {
                    case 'SPAN' :
                        input =
                            <HTMLElement>
                            d3.select(parent)
                                .append('input')
                                .attr('type', 'text')
                                .attr('name', name)
                                .attr('value', (<any>fmt)[name])
                                .attr('pattern', elt.getAttribute('data-pattern'))
                                .attr('required', true)
                                .node()
                        ;
                        break;
                    case 'UL' :
                        let txt: string = '';
                        const re = new RegExp(elt.getAttribute('data-line_pattern'));
                        elt.querySelectorAll('li').forEach((li: HTMLLIElement) => {
                            const res = re.exec(li.innerText);
                            for (let i = 1 ; i<res.length ; i++)
                                txt += res[i];
                            txt += '\n';
                        })
                        txt = txt.trim();
                        input =
                            <HTMLElement>
                            d3.select(parent)
                                .append('textarea')
                                .attr('name', name)
                                .attr('data-line_pattern', elt.getAttribute('data-line_pattern'))
                                .text(txt)
                                .on('input', (d, i, g) => PrintOptionsEditor.checkTextareaLines(<HTMLTextAreaElement>g[i]))
                                .node()
                        ;
                        break;

                }
                parent.replaceChild(input, <HTMLElement>g[i]);
            });
    }

    private deleteFormat(fmt: Format, i: number, g: HTMLDivElement[]) {
        const url = `${this.absUrl}/printingOptions/printoffer/removeOfferItem`;
        const params = new FormData();
        params.append('section', 'formats')
        params.append('index:int', Number(i).toString(10));
        d3.json(url, {body: params, method: 'POST'})
            .then(() => {
                const height = g[i].getBoundingClientRect().height;
                d3.select(g[i])
                    .style('height', `${height}px`)
                    .style('opacity', '1')
                    .style('overflow', 'hidden')
                    .transition().duration(TR_DURATION)
                    .style('height', '0px')
                    .style('opacity', '0')
                    .remove()
                ;
            });
    }

    private saveFormat(fmt: Format, i: number, g: HTMLDivElement[]) {
        const inpustok =
            d3.select(g[i]).selectAll('input').nodes()
                .map<boolean>((elt: HTMLInputElement) => elt.validity.valid)
                .reduce((a, b) => a && b, true);

        const textareasok =
            d3.select(g[i]).selectAll('textarea').nodes()
                .map<boolean>((elt: HTMLTextAreaElement) => PrintOptionsEditor.checkTextareaLines(elt))
                .reduce((a, b) => a && b, true);

        const ok = inpustok && textareasok;
        if (ok) {
            let kv: {[name:string] : string} = {};
            d3.select(g[i]).selectAll('input, textarea')
                .each((d, i, g) => {
                    const input = <HTMLInputElement|HTMLTextAreaElement>g[i];
                    kv[input.name] = input.value;
                });
            console.log(kv);
            let req = new XMLHttpRequest();
            req.open('POST', `${this.absUrl}/printingOptions/printoffer/saveOfferItem`)
            req.addEventListener('load', ev => {
                const resp = <XMLHttpRequest>(ev.target);
                if (resp.status == 200) {
                    const updated = <Format>JSON.parse(resp.responseText);
                    let data = <Format[]>d3.select(this.formatsWrapper).select('div.formats')
                        .selectAll('div').data();
                    data.splice(i,1, updated);
                    this.updateFormats(data);
                }

            })
            const formdata = new FormData();
            formdata.append('section', 'formats');
            formdata.append('index:int', Number(i).toString(10));
            formdata.append('jsondata', JSON.stringify(kv));
            req.send(formdata);
        }
    }

    private static checkTextareaLines(ta: HTMLTextAreaElement): boolean {
        const lines: string[] = ta.value.split('\n');
        const reline = new RegExp(ta.getAttribute('data-line_pattern'));
        for (let line of lines) {
            if (!reline.test(line)) {
                ta.classList.add('invalid');
                return false;
            }
            else {
                ta.classList.remove('invalid');
            }
        }
        return true;
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
        .then(
            () => new PrintOptionsEditor(document.body.getAttribute('data-absolute_url')));
}

window.addEventListener('load', () => main());