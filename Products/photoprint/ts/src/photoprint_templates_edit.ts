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

type Finish = {
    reference: string,
    label: I18NString,
    description: I18NString,
    price: number,
    frames: string[]
}

type Frame = {
    reference: string,
    label: I18NString,
    description: I18NString,
    price: number,
}

type PrintInfos = {
    formats: Format[],
    finishes: Finish[]
};

class PrintOptionsEditor {
    private static FORMATS_SECTION = 0;
    private static FINISHES_SECTION = 1;
    private static FRAMES_SECTION = 2;

    private static SECTIONS_INFOS = [
        {
            section: 'formats',
            btnTitle: _("Add new format…"),
            html: PrintOptionsEditor.formatViewHtml
        },
        {
            section: 'finishes',
            btnTitle: _("Add new finish…"),
            html: PrintOptionsEditor.finishViewHtml
        },
        {
            section: 'frames',
            btnTitle: _("Add new frame…"),
            html: PrintOptionsEditor.frameViewHtml
        },
    ]

    private absUrl: string;
    // private avirer_formatsWrapper: HTMLTableDataCellElement;
    private cells: NodeListOf<HTMLTableDataCellElement>;

    constructor(absUrl: string) {
        this.absUrl = absUrl;
        /*let avirer_cells = */
        this.cells = document.querySelectorAll<HTMLTableDataCellElement>('#print_options_editor > tr > td');
        // this.avirer_formatsWrapper = avirer_cells[0];

        this.initWrappersAndButtons();
        d3.json(`${this.absUrl}/printingOptions/printoffer/json`)
            .then((infos: PrintInfos) => {
                for (let i = 0; i < PrintOptionsEditor.SECTIONS_INFOS.length; i++) {
                    this.updateSection(i, (<any>infos)[PrintOptionsEditor.SECTIONS_INFOS[i].section])
                }
            })
    }

    private initWrappersAndButtons() {
        let cells = document.querySelectorAll<HTMLTableDataCellElement>('#print_options_editor > tr > td');
        const infos = PrintOptionsEditor.SECTIONS_INFOS;
        for (let i = 0; i < infos.length; i++) {
            d3.select(cells[i])
                .append('div')
                .attr('class', infos[i].section)
            ;
            d3.select(cells[i])
                .append('div')
                .attr('class', 'buttons')
                .append('a')
                .on('click', () => this.createItem(i))
                .attr('href', '#')
                .attr('title', infos[i].btnTitle)
                .append('i')
                .attr('class', 'fas fa-plus')
            ;
        }
    }

    private updateSection(sectionIndex: number, data: any, editLast = false) {
        const updateSel = d3.select(this.cells[sectionIndex])
            .select(`div.${PrintOptionsEditor.SECTIONS_INFOS[sectionIndex].section}`)
            .selectAll('div')
            .data(data);
        const enterSel = updateSel.enter().append('div');
        const exitSel = updateSel.exit().remove();


        enterSel.merge(updateSel)
            // @ts-ignore
            .html(PrintOptionsEditor.SECTIONS_INFOS[sectionIndex].html)
            .on('click', (d: any, i: number, g: HTMLDivElement[]) => {
                this.onItemClick(sectionIndex, d, i, g);
            })
        ;

        if (editLast) {
            const editbtn: HTMLElement =
                <HTMLElement>d3.select(this.cells[sectionIndex])
                    .select(`div.${PrintOptionsEditor.SECTIONS_INFOS[sectionIndex].section} > div:last-child i.btn.edit`)
                    .node();
            editbtn.dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));
            d3.select(this.cells[sectionIndex])
                .select(`div.${PrintOptionsEditor.SECTIONS_INFOS[sectionIndex].section} > div:last-child input`)
                .call((s) => (<HTMLInputElement>s.node()).focus())
            ;
        }
    }

    // private avirer_updateFormats(formats: Array<Format>, editLast = false) {
    //     const formatUpdate = d3.select(this.avirer_formatsWrapper).select('div.formats').selectAll('div')
    //         .data(formats);
    //     const formatEnter = formatUpdate.enter().append('div')
    //     const formatExit = formatUpdate.exit().remove();
    //
    //     formatEnter.merge(formatUpdate)
    //         .html((d: Format, i: number) => PrintOptionsEditor.formatViewHtml(d, i))
    //         .on('click', (d: Format, i: number, g: Array<HTMLDivElement>) => {
    //             this.avirer_onFormatClick(d, i, g);
    //         })
    //     ;
    //     if (editLast) {
    //         const editbtn: HTMLElement =
    //             <HTMLElement>
    //                 d3.select(this.avirer_formatsWrapper).select('div.formats > div:last-child i.btn.edit').node();
    //         editbtn.dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));
    //         d3.select(this.avirer_formatsWrapper).select('div.formats > div:last-child input')
    //             .call((s) => (<HTMLInputElement>s.node()).focus())
    //         ;
    //     }
    // }

    private static htmlViewLayout(htmlrows: string): string {
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
              ${htmlrows}
           </table>
        `;
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
        const rows = `
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
          </tr>`;
        return PrintOptionsEditor.htmlViewLayout(rows);
    }


    private static finishViewHtml(finish: Finish): string {
        const label = Object.entries(finish.label)
            .map(([lang, value]) => `<li>${value}@${lang}</li>`)
            .reduce((a, b) => a + b, '');

        const description = Object.entries(finish.description)
            .map(([lang, value]) => `<li>${value}@${lang}</li>`)
            .reduce((a, b) => a + b, '');

        const rows = `
          <tr>
            <th>${_("Reference")}</th>
            <td>
              <span data-name="reference" data-pattern=".+">${finish.reference}</span>
            </td>
          </tr>
          <tr>
            <th>${_("Label")}</th>
            <td>
              <ul data-name="label" data-line_pattern="(.*)(@)(\\w\\w)$">${label}</ul>
            </td>
          </tr>
          <tr>
            <th>${_("Description")}</th>
            <td>
              <ul data-name="description" data-line_pattern="(.*)(@)(\\w\\w)$">${description}</ul>
            </td>
          </tr>
          <tr>
            <th>${_("Price")}</th>
            <td>
              <span data-name="price" data-pattern="^\\d+$">${finish.price}</span> ${_("€ ET")}
            </td>
          </tr>
          
        `;
        return PrintOptionsEditor.htmlViewLayout(rows);
    }

    private static frameViewHtml(frame: Finish): string {
        const label = Object.entries(frame.label)
            .map(([lang, value]) => `<li>${value}@${lang}</li>`)
            .reduce((a, b) => a + b, '');

        const description = Object.entries(frame.description)
            .map(([lang, value]) => `<li>${value}@${lang}</li>`)
            .reduce((a, b) => a + b, '');

        const rows = `
          <tr>
            <th>${_("Reference")}</th>
            <td>
              <span data-name="reference" data-pattern=".+">${frame.reference}</span>
            </td>
          </tr>
          <tr>
            <th>${_("Label")}</th>
            <td>
              <ul data-name="label" data-line_pattern="(.*)(@)(\\w\\w)$">${label}</ul>
            </td>
          </tr>
          <tr>
            <th>${_("Description")}</th>
            <td>
              <ul data-name="description" data-line_pattern="(.*)(@)(\\w\\w)$">${description}</ul>
            </td>
          </tr>
          <tr>
            <th>${_("Price")}</th>
            <td>
              <span data-name="price" data-pattern="^\\d+$">${frame.price}</span> ${_("€ ET")}
            </td>
          </tr>
          
        `;
        return PrintOptionsEditor.htmlViewLayout(rows);
    }

    // private avirer_onFormatClick(fmt: Format, i: number, g: HTMLDivElement[]) {
    //     const evt = d3.event;
    //     const target = evt.target;
    //     if (target.classList.contains('btn')) {
    //         evt.stopPropagation();
    //         evt.preventDefault();
    //         if (target.classList.contains('edit')) {
    //             target.classList.remove('edit');
    //             target.classList.add('validate');
    //             target.parentElement.setAttribute('title', _("Save"));
    //             this.avirer_startEdit(fmt, i, g);
    //         } else if (target.classList.contains('delete'))
    //             this.deleteFormat(fmt, i, g);
    //         else if (target.classList.contains('validate'))
    //             this.avirer_saveFormat(fmt, i, g);
    //     }
    // }

    // private avirer_startEdit(fmt: Format, i: number, g: HTMLDivElement[]) {
    //     d3.select(g[i]).selectAll('*[data-name]')
    //         .each((d, i, g) => {
    //             const elt = <HTMLElement>g[i];
    //             const name = (elt.getAttribute('data-name'));
    //             const parent = elt.parentElement;
    //             let input: HTMLElement;
    //             switch (elt.tagName) {
    //                 case 'SPAN' :
    //                     input =
    //                         <HTMLElement>
    //                             d3.select(parent)
    //                                 .append('input')
    //                                 .attr('type', 'text')
    //                                 .attr('name', name)
    //                                 .attr('value', (<any>fmt)[name])
    //                                 .attr('pattern', elt.getAttribute('data-pattern'))
    //                                 .attr('required', true)
    //                                 .node()
    //                     ;
    //                     break;
    //                 case 'UL' :
    //                     let txt: string = '';
    //                     const re = new RegExp(elt.getAttribute('data-line_pattern'));
    //                     elt.querySelectorAll('li').forEach((li: HTMLLIElement) => {
    //                         const res = re.exec(li.innerText);
    //                         for (let i = 1; i < res.length; i++)
    //                             txt += res[i];
    //                         txt += '\n';
    //                     })
    //                     txt = txt.trim();
    //                     input =
    //                         <HTMLElement>
    //                             d3.select(parent)
    //                                 .append('textarea')
    //                                 .attr('name', name)
    //                                 .attr('data-line_pattern', elt.getAttribute('data-line_pattern'))
    //                                 .text(txt)
    //                                 .on('input', (d, i, g) => PrintOptionsEditor.checkTextareaLines(<HTMLTextAreaElement>g[i]))
    //                                 .node()
    //                     ;
    //                     break;
    //
    //             }
    //             parent.replaceChild(input, <HTMLElement>g[i]);
    //         });
    // }

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

    // private avirer_saveFormat(fmt: Format, i: number, g: HTMLDivElement[]) {
    //     const inpustok =
    //         d3.select(g[i]).selectAll('input').nodes()
    //             .map<boolean>((elt: HTMLInputElement) => elt.validity.valid)
    //             .reduce((a, b) => a && b, true);
    //
    //     const textareasok =
    //         d3.select(g[i]).selectAll('textarea').nodes()
    //             .map<boolean>((elt: HTMLTextAreaElement) => PrintOptionsEditor.checkTextareaLines(elt))
    //             .reduce((a, b) => a && b, true);
    //
    //     const ok = inpustok && textareasok;
    //     if (ok) {
    //         let kv: { [name: string]: string } = {};
    //         d3.select(g[i]).selectAll('input, textarea')
    //             .each((d, i, g) => {
    //                 const input = <HTMLInputElement | HTMLTextAreaElement>g[i];
    //                 kv[input.name] = input.value;
    //             });
    //         console.log(kv);
    //         let req = new XMLHttpRequest();
    //         req.open('POST', `${this.absUrl}/printingOptions/printoffer/saveOfferItem`)
    //         req.addEventListener('load', ev => {
    //             const resp = <XMLHttpRequest>(ev.target);
    //             if (resp.status == 200) {
    //                 const updated = <Format>JSON.parse(resp.responseText);
    //                 let data = <Format[]>d3.select(this.avirer_formatsWrapper).select('div.formats')
    //                     .selectAll('div').data();
    //                 data.splice(i, 1, updated);
    //                 this.avirer_updateFormats(data);
    //             }
    //
    //         })
    //         const formdata = new FormData();
    //         formdata.append('section', 'formats');
    //         formdata.append('index:int', Number(i).toString(10));
    //         formdata.append('jsondata', JSON.stringify(kv));
    //         req.send(formdata);
    //     }
    // }

    private static checkTextareaLines(ta: HTMLTextAreaElement): boolean {
        const lines: string[] = ta.value.split('\n');
        const reline = new RegExp(ta.getAttribute('data-line_pattern'));
        for (let line of lines) {
            if (!reline.test(line)) {
                ta.classList.add('invalid');
                return false;
            } else {
                ta.classList.remove('invalid');
            }
        }
        return true;
    }

    private createItem(sectionIndex: number) {
        const evt = d3.event;
        evt.stopPropagation();
        evt.preventDefault();
        console.log('createItem', sectionIndex);

        let params: FormData = new FormData();
        params.append('section', PrintOptionsEditor.SECTIONS_INFOS[sectionIndex].section);
        let url = `${this.absUrl}/printingOptions/printoffer/getTemplate`;
        d3.json(
            url,
            {
                body: params,
                method: 'POST'
            }
        ).then((format: Format) => {
            let data = d3.select(this.cells[sectionIndex])
                .select(`div.${PrintOptionsEditor.SECTIONS_INFOS[sectionIndex].section}`)
                .selectAll('div').data();
            data.push(format);
            this.updateSection(sectionIndex, data, true);
        });
    }

    private onItemClick(sectionIndex: number, d: any, i: number, g: HTMLDivElement[]) {
        const evt = d3.event;
        const target = evt.target;
        if (target.classList.contains('btn')) {
            evt.stopPropagation();
            evt.preventDefault();
            if (target.classList.contains('edit')) {
                target.classList.remove('edit');
                target.classList.add('validate');
                target.parentElement.setAttribute('title', _("Save"));
                this.startEditItem(sectionIndex, d, i, g);
            } else if (target.classList.contains('delete')) {
                this.removeItem(sectionIndex, i, g);
            } else if (target.classList.contains('validate')) {
                this.saveItem(sectionIndex, i, g);
            }
        }
    }

    private startEditItem(sectionIndex: number, data: any, i: number, g: HTMLDivElement[]) {
        d3.select(g[i]).selectAll('*[data-name]')
            .each((_, i_, g_) => {
                const elt = <HTMLElement>g_[i_];
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
                                    .attr('value', (<any>data)[name])
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
                            for (let j = 1; j < res.length; j++)
                                txt += res[j];
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
                parent.replaceChild(input, elt);
            });
    }

    private saveItem(sectionIndex: number, i: number, g: HTMLDivElement[]) {
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
            let kv: { [name: string]: string } = {};
            d3.select(g[i]).selectAll('input, textarea')
                .each((d, i, g) => {
                    const input = <HTMLInputElement | HTMLTextAreaElement>g[i];
                    kv[input.name] = input.value;
                });

            let req = new XMLHttpRequest();
            req.open('POST', `${this.absUrl}/printingOptions/printoffer/saveOfferItem`)
            req.addEventListener('load', ev => {
                const resp = <XMLHttpRequest>(ev.target);
                if (resp.status == 200) {
                    const updated = JSON.parse(resp.responseText);
                    let data = <[any]>d3.select(this.cells[sectionIndex])
                        .select(`div.${PrintOptionsEditor.SECTIONS_INFOS[sectionIndex].section}`)
                        .selectAll('div').data();
                    data.splice(i, 1, updated);
                    this.updateSection(sectionIndex, data);
                }

            })
            const formdata = new FormData();
            formdata.append('section', PrintOptionsEditor.SECTIONS_INFOS[sectionIndex].section);
            formdata.append('index:int', Number(i).toString(10));
            formdata.append('jsondata', JSON.stringify(kv));
            req.send(formdata);
        }

    }

    private removeItem(sectionIndex: number, i: number, g: HTMLDivElement[]) {
        const url = `${this.absUrl}/printingOptions/printoffer/removeOfferItem`;
        const params = new FormData();
        params.append('section', PrintOptionsEditor.SECTIONS_INFOS[sectionIndex].section);
        params.append('index:int', Number(i).toString(10));
        d3.json(url, {body: params, method: 'POST'})
            .then((res: { ack: boolean }) => {
                if (res.ack) {
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
                }
            });
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