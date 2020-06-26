import * as d3 from "d3";
import i18next, {TOptions} from "i18next";
import HttpApi from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector'

const _ = (s: string, options?: TOptions): string => i18next.t(s, options);
const TR_DURATION = 500; // ms

type AnySel = d3.Selection<HTMLElement, any, HTMLElement, any>;
type PrintOfferItemSel = d3.Selection<SVGForeignObjectElement, PrintOfferItem, undefined, unknown>;
type I18NString = { [lang: string]: string };

interface PriceRange {
    start: number;
    stop: number;
    price: number;
}

interface PrintOfferItem {
    reference: string;
    label: I18NString;
    price: number;
}

interface Format extends PrintOfferItem {
    short_edge: number,
    long_edge: number,
    copies: number,
    prices_ranges: PriceRange[],
    finishes: string[],
}

interface Finish extends PrintOfferItem {
    description: I18NString,
    frames: string[]
}


interface Frame extends PrintOfferItem {
    description: I18NString,
}

interface PrintInfos {
    formats: Format[];
    finishes: Finish[];
    frames: Frame[];
}

interface SectionInfo {
    section: string;
    btnTitle: string;
    html: (item: PrintOfferItem) => string;
}


const FLOAT_PATTERN = '^\\s*\\d+[\\.,]?\\d*\\s*$'

class PrintOptionsEditor {
    private static COLS_MARGIN = 50;
    private static ROW_MARGIN = 5;
    private static FORMATS_SECTION = 0;
    private static FINISHES_SECTION = 1;
    private static FRAMES_SECTION = 2;

    private absUrl: string;
    private cells: NodeListOf<HTMLTableDataCellElement>;
    private readonly SECTIONS_INFOS: SectionInfo[];
    private htmlTmpShape: AnySel;
    private colwidth: number;
    private editorSelector: string;

    constructor(absUrl: string, editorSelector: string) {
        this.SECTIONS_INFOS = [
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
        this.absUrl = absUrl;
        this.editorSelector = editorSelector;

        const wrapper = document.querySelector<HTMLDivElement>(this.editorSelector);
        const wrapperRect = wrapper.getBoundingClientRect();
        this.colwidth = (wrapperRect.width - PrintOptionsEditor.COLS_MARGIN * (this.SECTIONS_INFOS.length - 1)) / this.SECTIONS_INFOS.length;
        this.htmlTmpShape = <AnySel>d3.select(editorSelector)
            .append('div')
            .style('position', 'absolute')
            .style('width', `${this.colwidth}px`)


        d3.select(editorSelector)
            .append('svg:svg')
            .attr('width', `${wrapperRect.width}px`)
            .attr('height', '0px')
            .selectAll('g')
            .data<SectionInfo>(this.SECTIONS_INFOS)
            .enter()
            .append('g')
            .attr('transform', (d, i) => `translate(${i * (this.colwidth + PrintOptionsEditor.COLS_MARGIN)},0)`)
            .attr('class', (d) => `section ${d.section}`)
        ;
        // console.log(document.querySelector('svg'));
        d3.json(`${this.absUrl}/printingOptions/printoffer/json`)
            .then((infos: PrintInfos) => {
                d3.select(editorSelector)
                    .selectAll<SVGGElement, SectionInfo>('g.section')
                    .each((d: SectionInfo, i, g) =>
                        this.updateSection(d,
                            <PrintOfferItem[]>(<any>infos)[this.SECTIONS_INFOS[i].section],
                            g[i]))
                ;
                this.updateLayout();
            })
        ;
    }

    private getHtmlHeight(html: string): number {
        this.htmlTmpShape.html(html)
        const height = this.htmlTmpShape.node().getBoundingClientRect().height;
        this.htmlTmpShape.html('')
        return height;
    }

    // private initWrappersAndButtons() {
    //     let cells = document.querySelectorAll<HTMLTableDataCellElement>('#print_options_editor > tr > td');
    //     const infos = this.SECTIONS_INFOS;
    //     for (let i = 0; i < infos.length; i++) {
    //         d3.select(cells[i])
    //             .append('div')
    //             .attr('class', infos[i].section)
    //         ;
    //         d3.select(cells[i])
    //             .append('div')
    //             .attr('class', 'buttons')
    //             .append('a')
    //             .on('click', () => this.createItem(i))
    //             .attr('href', '#')
    //             .attr('title', infos[i].btnTitle)
    //             .append('i')
    //             .attr('class', 'fas fa-plus')
    //         ;
    //     }
    // }

    private updateSection(sectionInfo: SectionInfo,
                          items: PrintOfferItem[],
                          parentElt: SVGGElement,
                          editLast = false) {
        const updateSel = d3.select(parentElt)
            .selectAll('foreignObject')
            .data(items);
        const enterSel = updateSel.enter().append('foreignObject');
        enterSel.append('xhtml:div');
        const exitSel = updateSel.exit().remove();

        enterSel.merge(updateSel)
            .each((item: PrintOfferItem, i, g) => {
                this.updateItemView(sectionInfo, <PrintOfferItemSel>d3.select(g[i]))
            })
        ;
    }

    private updateItemView(sectionInfo: SectionInfo, itemSel: PrintOfferItemSel) {
        const html = sectionInfo.html(itemSel.datum());
        const height = this.getHtmlHeight(html);
        itemSel.select('div') // item ui
            .style('width', `${this.colwidth}px`)
            .style('height', `${height}px`)
            .html(html)
            .on('click', () => {
                this.onItemClick(itemSel)
            })
        ;
        itemSel // foreignObject need to be sized explicitly
            .attr('width', `${this.colwidth}px`)
            .attr('height', `${height}px`)
        ;
    }

    private updateLayout() {
        let svgheight = parseFloat(d3.select(this.editorSelector).select('svg').attr('height'));
        d3.select(this.editorSelector)
            .selectAll('g')
            .each((d, i, g) => {
                const heights: number[] =
                    d3.select(g[i]).selectAll('foreignObject > div').nodes().map((node: HTMLDivElement) => parseFloat(node.style.height));

                const colheight = heights.reduce((a, b) => a + b, 0) + PrintOptionsEditor.ROW_MARGIN * heights.length;
                if (svgheight < colheight) {
                    svgheight = colheight;
                    d3.select(this.editorSelector).select('svg')
                        .attr('height', `${svgheight}px`);
                }

                d3.select(g[i]).selectAll('foreignObject')
                    .each((_, ii, gg) => {
                        let y = heights.slice(0, ii).reduce((a, b) => a + b, 0);
                        y += ii * PrintOptionsEditor.ROW_MARGIN;
                        d3.select(gg[ii])
                            .transition().duration(TR_DURATION)
                            .attr('transform', `translate(0, ${y})`)
                        ;
                    })
            })
        ;
    }

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

    private static formatViewHtml(item: PrintOfferItem): string {
        const fmt = <Format>item;
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
              <span data-name="short_edge" data-pattern="${FLOAT_PATTERN}">${fmt.short_edge}</span> cm
            </td>
          </tr>
          <tr>
            <th>${_("Long edge")}</th>
            <td>
              <span data-name="long_edge" data-pattern="${FLOAT_PATTERN}">${fmt.long_edge}</span> cm
            </td>
          </tr>
          <tr>
            <th>${_("Price")}</th>
            <td>
              <span data-name="price" data-pattern="${FLOAT_PATTERN}">${fmt.price}</span> ${_("€ ET")}
            </td>
          </tr>
          <tr>
            <th>${_("Scarcity")}</th>
            <td>
              <ul data-name="prices_ranges"
                  data-line_pattern="^\\s*$|^\\s*(\\[)\\s*(\\d+)\\s*(,\\s*)(\\d+)\\s*(\\])(\\s*)(\\d+[\\.,]?\\d*)\\s*$">${prices_ranges}</ul>
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


    private static finishViewHtml(item: PrintOfferItem): string {
        const finish = <Finish>item;
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
              <span data-name="price" data-pattern="${FLOAT_PATTERN}">${finish.price}</span> ${_("€ ET")}
            </td>
          </tr>
          
        `;
        return PrintOptionsEditor.htmlViewLayout(rows);
    }

    private static frameViewHtml(item: PrintOfferItem): string {
        const frame = <Frame>item;
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
              <span data-name="price" data-pattern="${FLOAT_PATTERN}">${frame.price}</span> ${_("€ ET")}
            </td>
          </tr>
          
        `;
        return PrintOptionsEditor.htmlViewLayout(rows);
    }

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

    // private createItem(sectionIndex: number) {
    //     const evt = d3.event;
    //     evt.stopPropagation();
    //     evt.preventDefault();
    //     console.log('createItem', sectionIndex);
    //
    //     let params: FormData = new FormData();
    //     params.append('section', this.SECTIONS_INFOS[sectionIndex].section);
    //     let url = `${this.absUrl}/printingOptions/printoffer/getTemplate`;
    //     d3.json(
    //         url,
    //         {
    //             body: params,
    //             method: 'POST'
    //         }
    //     ).then((format: Format) => {
    //         let data = d3.select(this.cells[sectionIndex])
    //             .select(`div.${this.SECTIONS_INFOS[sectionIndex].section}`)
    //             .selectAll('div').data();
    //         data.push(format);
    //         this.updateSection(sectionIndex, data, true);
    //     });
    // }

    private onItemClick(itemSel: PrintOfferItemSel) {
        const evt = d3.event;
        const target = evt.target;
        if (target.classList.contains('btn')) {
            evt.stopPropagation();
            evt.preventDefault();
            if (target.classList.contains('edit')) {
                target.classList.remove('edit');
                target.classList.add('validate');
                target.parentElement.setAttribute('title', _("Save"));
                this.startEditItem(itemSel);
            } else if (target.classList.contains('delete')) {
                this.removeItem(itemSel);
            } else if (target.classList.contains('validate')) {
                this.saveItem(itemSel);
            }
        }
    }

    private startEditItem(itemSel: PrintOfferItemSel) {
        const itemD = itemSel.datum();
        itemSel.selectAll('*[data-name]')
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
                                    .attr('value', (<any>itemD)[name])
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
        const height = this.getHtmlHeight(itemSel.select('div').style('height', undefined).html())
        itemSel.select('div')
            .style('height', `${height}px`)
        ;
        itemSel
            .attr('height', `${height}px`)
        ;
        this.updateLayout();
    }

    private saveItem(itemSel: PrintOfferItemSel/*sectionIndex: number, i: number, g: HTMLDivElement[]*/) {
        const inpustok =
            itemSel.selectAll('input').nodes()
                .map<boolean>((elt: HTMLInputElement) => elt.validity.valid)
                .reduce((a, b) => a && b, true);

        const textareasok =
            itemSel.selectAll('textarea').nodes()
                .map<boolean>((elt: HTMLTextAreaElement) => PrintOptionsEditor.checkTextareaLines(elt))
                .reduce((a, b) => a && b, true);

        if (inpustok && textareasok) {
            let kv: { [name: string]: string } = {};
            itemSel.selectAll('input, textarea')
                .each((d, i, g) => {
                    const input = <HTMLInputElement | HTMLTextAreaElement>g[i];
                    kv[input.name] = input.value;
                })
            ;
            const sectionSel = d3.select(itemSel.node().parentElement);
            const sectionData = <PrintOfferItem[]>sectionSel.selectAll('foreignObject').data();

            let req = new XMLHttpRequest();
            req.open('POST', `${this.absUrl}/printingOptions/printoffer/saveOfferItem`)
            req.addEventListener('load', ev => {
                const resp = <XMLHttpRequest>(ev.target);
                if (resp.status == 200) {
                    const updated = JSON.parse(resp.responseText);
                    itemSel.datum(updated);
                    this.updateItemView(<SectionInfo>sectionSel.datum(), itemSel)
                    this.updateLayout();
                }

            })
            let itemIndex: number;
            for (itemIndex = 0; itemIndex <= sectionData.length; itemIndex++) {
                if (itemSel.datum() === sectionData[itemIndex])
                    break;
            }

            if (itemIndex === sectionData.length) {
                console.error('item to be saved not found');
                return;
            }

            const formdata = new FormData();
            formdata.append('section', (<SectionInfo>sectionSel.datum()).section);
            formdata.append('index:int', Number(itemIndex).toString(10));
            formdata.append('jsondata', JSON.stringify(kv));
            req.send(formdata);
        }

    }

    private removeItem(itemSel: PrintOfferItemSel/*section:string, itemIndex: number, itemUIElt: HTMLDivElement*/) {
        const sectionSel = d3.select(itemSel.node().parentElement);
        const sectionData = <PrintOfferItem[]>sectionSel.selectAll('foreignObject').data();
        let itemIndex: number;
        for (itemIndex = 0; itemIndex <= sectionData.length; itemIndex++) {
            if (itemSel.datum() === sectionData[itemIndex])
                break;
        }
        if (itemIndex === sectionData.length) {
            console.error('item to be removed not found');
            return;
        }

        const url = `${this.absUrl}/printingOptions/printoffer/removeOfferItem`;
        const params = new FormData();
        params.append('section', (<SectionInfo>sectionSel.datum()).section);
        params.append('index:int', Number(itemIndex).toString(10));
        d3.json(url, {body: params, method: 'POST'})
            .then((res: { ack: boolean }) => {
                if (res.ack) {
                    itemSel.style('opacity', '1')
                        .transition().duration(TR_DURATION)
                        .style('opacity', '0')
                        .remove()
                        .on('end', () => this.updateLayout())
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
            () => new PrintOptionsEditor(document.body.getAttribute('data-absolute_url'), '#print_options_editor'));
}

window.addEventListener('load', () => main());