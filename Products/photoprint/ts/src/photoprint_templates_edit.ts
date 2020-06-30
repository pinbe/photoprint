import * as d3 from "d3";
import i18next, {TOptions} from "i18next";
import HttpApi from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector'

const _ = (s: string, options?: TOptions): string => i18next.t(s, options);
const TR_DURATION = 500; // ms

type AnySel = d3.Selection<HTMLElement, any, HTMLElement, any>;
type PrintOfferItemSel = d3.Selection<SVGForeignObjectElement, IPrintOfferItem, undefined, unknown>;
type I18NString = { [lang: string]: string };

interface PriceRange {
    start: number;
    stop: number;
    price: number;
}

interface IPrintOfferItem {
    reference: string;
    label: I18NString;
    price: number;
}

interface Format extends IPrintOfferItem {
    short_edge: number,
    long_edge: number,
    copies: number,
    prices_ranges: PriceRange[],
    finishes: string[],
}

interface Finish extends IPrintOfferItem {
    description: I18NString,
    frames: string[]
}


interface Frame extends IPrintOfferItem {
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
    title: string;
    html: (item: IPrintOfferItem) => string;
}

class Link {
    private from: PrintOfferItem;
    private to: PrintOfferItem;
    private arc: d3.Selection<SVGPathElement, Link, any, any>;

    constructor(from: PrintOfferItem,
                to: PrintOfferItem,
                arc: d3.Selection<SVGPathElement, Link, any, any>) {
        this.from = from;
        this.to = to;
        this.arc = arc.datum(this);
    }

    updatePath() {
        this.arc
            .transition().duration(TR_DURATION)
            .attr('d', Bézier(this.from.getOutletPosition(), this.to.getInletPosition()))
        ;
    }
}

class PrintOfferItem implements IPrintOfferItem {
    label: I18NString;
    price: number;
    reference: string;
    private editor: PrintOptionsEditor;
    private sectionInfo: SectionInfo;
    private sel: d3.Selection<SVGForeignObjectElement, PrintOfferItem, any, any>;
    private outlet: d3.Selection<SVGPathElement, PrintOfferItem, any, any>;
    private inlet: d3.Selection<SVGPathElement, PrintOfferItem, any, any>;
    private incomingLinks: {[reference: string]: Link};
    private position: Coords2D;

    constructor(editor: PrintOptionsEditor,
                sectionInfo: SectionInfo,
                itemJsonData: IPrintOfferItem) {
        this.updateData(itemJsonData);
        this.editor = editor;
        this.sectionInfo = sectionInfo;
        this.sel = null;
        this.outlet = null;
        this.inlet = null;
        this.incomingLinks = {};
        this.position = {x:0, y:0};
    }

    private updateData(itemJsonData: IPrintOfferItem) {
        for (let [name, value] of Object.entries(itemJsonData))
            (<any>this)[name] = value;
    }

    draw(fo: SVGForeignObjectElement) {
        this.sel = d3.select(fo);
        const html = this.sectionInfo.html(this);
        const height = this.editor.getHtmlHeight(html);
        const width = this.editor.colwidth;
        this.sel.select('div') // item ui
            .style('width', `${width}px`)
            .style('height', `${height}px`)
            .html(html)
            .on('click', () => {
                this.onClick();
            })
        ;
        this.sel
            // foreignObject need to be sized explicitly
            .attr('width', `${width}px`)
            .attr('height', `${height}px`)
        ;
        if (this.sectionInfo.section !== 'frames' && this.outlet === null) {
            this.outlet = this.editor.arcsSel
                .append<SVGPathElement>('path')
                .datum(this)
                .attr('class', `plug outlet ${this.sectionInfo.section}`)
                .attr('d', 'M0-8A8,8,0,0,1,8,0,8,8,0,0,1,0,8Z')
                .attr('transform', `translate(${width}, ${height / 2})`)
            ;
            const d = d3.drag();
            d.on('start', () => this.onDragStart());
            this.outlet.call(d);
        }
        if (this.sectionInfo.section !== 'formats' && this.inlet === null) {
            this.inlet = this.editor.arcsSel
                .append<SVGPathElement>('path')
                .datum(this)
                .attr('class', `plug inlet ${this.sectionInfo.section}`)
                .attr('d', 'M0-8A8,8,0,0,1,8,0,8,8,0,0,1,0,8Z')
                .attr('transform', `translate(0, ${height / 2}) rotate(180)`)
            ;
        }
    }

    private onDragStart() {
        const origin: d3.D3DragEvent<SVGPathElement, PrintOfferItem, any> = d3.event;
        const arc = <d3.Selection<SVGPathElement, Link, any, any>>this.editor.arcsSel.append('path')
            .attr('class', 'link new')
        ;

        let endTargetSelector: string;
        switch (this.sectionInfo.section) {
            case 'formats' :
                endTargetSelector = '.plug.inlet.finishes';
                break;

            case 'finishes' :
                endTargetSelector = '.plug.inlet.frames';

        }
        let targetItem: PrintOfferItem = null;
        this.editor.arcsSel
            .selectAll(endTargetSelector)
            .on('mouseover', (d: PrintOfferItem) => targetItem = d)
            .on('mouseout', () => targetItem = null)
        ;

        d3.event.on('drag', () => {
            arc.attr('d', Bézier({x: origin.x, y: origin.y}, {x: d3.event.x, y: d3.event.y}))
        });
        d3.event.on('end', () => {
            if(targetItem === null)
                arc.remove();
            else
                // this.createLink(origin.subject, targetItem, arc);
                targetItem.createIncomingLink(this, arc);
        });
    }

    moveTo(x: number, y: number) {
        this.position.x = x;
        this.position.y = y;
        this.sel.transition().duration(TR_DURATION)
            .attr('transform', `translate(${x}, ${y})`)

        const rect = (<HTMLDivElement>this.sel.select('div').node()).getBoundingClientRect();
        if (this.outlet !== null)
            this.outlet.transition().duration(TR_DURATION)
                .attr('transform', `translate(${x + rect.width}, ${y + rect.height / 2})`)
            ;

        if (this.inlet !== null) {
            this.inlet.transition().duration(TR_DURATION)
                .attr('transform', `translate(${x}, ${y + rect.height / 2}) rotate(180)`)
            ;
            Object.values(this.incomingLinks).map(l=>l.updatePath());
        }

    }
    getInletPosition(): Coords2D|null {
        const rect = (<HTMLDivElement>this.sel.select('div').node()).getBoundingClientRect();
        if(this.inlet !== null) {
            return {x: this.position.x, y: this.position.y + rect.height/2}
        }
        return null;
    }

    getOutletPosition(): Coords2D|null {
        const rect = (<HTMLDivElement>this.sel.select('div').node()).getBoundingClientRect();
        if(this.outlet !== null) {
            return {x: this.position.x + rect.width, y: this.position.y + rect.height/2}
        }
        return null;
    }

    private onClick() {
        const evt = d3.event;
        const target = evt.target;
        if (target.classList.contains('btn')) {
            evt.stopPropagation();
            evt.preventDefault();
            if (target.classList.contains('edit')) {
                this.startEdit();
            } else if (target.classList.contains('delete')) {
                this.remove();
            } else if (target.classList.contains('validate')) {
                this.save();
            }
        }
    }

    startEdit(skipLayoutUpdate = false) {
        const btn = <HTMLElement>this.sel.select('i.btn.edit').node();
        btn.classList.remove('edit');
        btn.classList.add('validate');
        btn.parentElement.setAttribute('title', _("Save"));

        this.sel.selectAll('*[data-name]')
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
                                    .attr('value', (<any>this)[name])
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
        const height = this.editor.getHtmlHeight(this.sel.select('div').style('height', undefined).html())
        this.sel.select('div')
            .style('height', `${height}px`)
        ;
        this.sel
            .attr('height', `${height}px`)
        ;
        (<HTMLInputElement>this.sel.select('input').node()).focus();
        if (!skipLayoutUpdate)
            this.editor.updateLayout();

    }

    private remove() {
        const itemSel = this.sel;
        const sectionSel = d3.select(itemSel.node().parentElement);
        const sectionData = <IPrintOfferItem[]>sectionSel.selectAll('foreignObject.item').data();
        let itemIndex: number;
        for (itemIndex = 0; itemIndex <= sectionData.length; itemIndex++) {
            if (itemSel.datum() === sectionData[itemIndex])
                break;
        }
        if (itemIndex === sectionData.length) {
            console.error('item to be removed not found');
            return;
        }

        const url = `${this.editor.absUrl}/printingOptions/printoffer/removeOfferItem`;
        const params = new FormData();
        params.append('section', (<SectionInfo>sectionSel.datum()).section);
        params.append('index:int', Number(itemIndex).toString(10));
        d3.json(url, {body: params, method: 'POST'})
            .then((res: { ack: boolean }) => {
                if (res.ack) {
                    if (this.outlet)
                        this.outlet.style('opacity', '1')
                            .transition().duration(TR_DURATION)
                            .style('opacity', '0')
                            .remove()
                        ;
                    if (this.inlet)
                        this.inlet.style('opacity', '1')
                            .transition().duration(TR_DURATION)
                            .style('opacity', '0')
                            .remove()
                        ;
                    itemSel.style('opacity', '1')
                        .transition().duration(TR_DURATION)
                        .style('opacity', '0')
                        .remove()
                        .on('end', () => this.editor.updateLayout())
                    ;
                }
            });
    }

    private save() {
        const itemSel = this.sel;
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
            const sectionData = <IPrintOfferItem[]>sectionSel.selectAll('foreignObject.item').data();

            let req = new XMLHttpRequest();
            req.open('POST', `${this.editor.absUrl}/printingOptions/printoffer/saveOfferItem`)
            req.addEventListener('load', ev => {
                const resp = <XMLHttpRequest>(ev.target);
                if (resp.status == 200) {
                    const updated = JSON.parse(resp.responseText);
                    this.updateData(<IPrintOfferItem>updated);
                    this.draw(itemSel.node());
                    this.editor.updateLayout();
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

    public createIncomingLink(from: PrintOfferItem,
                              arc: d3.Selection<SVGPathElement, Link, any, any>) {
        if(!this.incomingLinks[from.reference]) {
            const link = new Link(from, this, arc);
            this.incomingLinks[from.reference] = link;
            link.updatePath();
        }
        else {
            arc.remove();
        }
    }
}

interface Coords2D {
    x: number;
    y: number;
}

function Bézier(from: Coords2D, to: Coords2D, strength: number = 2): string {
    const Δx = to.x - from.x;
    return `M${from.x} ${from.y} C${from.x + Δx / strength} ${from.y}, ${to.x - Δx / strength} ${to.y}, ${to.x} ${to.y}`;
}


const FLOAT_PATTERN = '^\\s*\\d+[\\.,]?\\d*\\s*$'

class PrintOptionsEditor {
    private static COLS_MARGIN = 100;
    private static ROW_MARGIN = 5;
    private static FORMATS_SECTION = 0;
    private static FINISHES_SECTION = 1;
    private static FRAMES_SECTION = 2;

    absUrl: string;
    private cells: NodeListOf<HTMLTableDataCellElement>;
    private readonly SECTIONS_INFOS: SectionInfo[];
    private htmlTmpShape: AnySel;
    colwidth: number;
    readonly editorSelector: string;
    private headerHeight: number;
    public readonly arcsSel: d3.Selection<SVGGElement, unknown, HTMLElement, any>;

    constructor(absUrl: string, editorSelector: string) {
        this.SECTIONS_INFOS = [
            {
                section: 'formats',
                title: _('Formats'),
                btnTitle: _("Add new format…"),
                html: PrintOptionsEditor.formatViewHtml
            },
            {
                section: 'finishes',
                title: _('Finishes'),
                btnTitle: _("Add new finish…"),
                html: PrintOptionsEditor.finishViewHtml
            },
            {
                section: 'frames',
                title: _('Frames'),
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


        const svg = d3.select(editorSelector)
            .append('svg:svg')
            .attr('width', `${wrapperRect.width}px`)
            .attr('height', '0px');

        // header
        this.headerHeight = 0;
        svg.append('g')
            .attr('class', 'cols-headers')
            .selectAll('foreignObject')
            .data(this.SECTIONS_INFOS)
            .enter()
            .append('foreignObject')
            .each((d, i, g) => {
                const html = `<div><h2>${d.title}</h2></div>`;
                const height = this.getHtmlHeight(html);
                this.headerHeight = (this.headerHeight < height) ? height : this.headerHeight;
                d3.select(g[i])
                    .attr('width', `${this.colwidth}px`)
                    .attr('height', `${height}px`)
                    .attr('transform', `translate(${i * (this.colwidth + PrintOptionsEditor.COLS_MARGIN)}, 0)`)
                    .html(html)
                ;
            })
        ;

        svg.append('g')
            .attr('class', 'printoffer-items')
            .selectAll('g')
            .data<SectionInfo>(this.SECTIONS_INFOS)
            .enter()
            .append('g')
            .attr('class', (d) => `section ${d.section}`)
        ;

        this.arcsSel = svg.append<SVGGElement>('g')
            .attr('class', 'links')
        ;

        d3.json(`${this.absUrl}/printingOptions/printoffer/json`)
            .then((infos: PrintInfos) => {
                d3.select(editorSelector)
                    .selectAll<SVGGElement, SectionInfo>('g.section')
                    .each((d: SectionInfo, i) =>
                        this.updateSection(d,
                            (<IPrintOfferItem[]>(<any>infos)[this.SECTIONS_INFOS[i].section])
                                .map<PrintOfferItem>(item => new PrintOfferItem(this, d, item))))
                ;
                this.updateLayout();
            })
        ;
    }

    getHtmlHeight(html: string): number {
        this.htmlTmpShape.html(html)
        const height = this.htmlTmpShape.node().getBoundingClientRect().height;
        this.htmlTmpShape.html('')
        return height;
    }

    private updateSection(sectionInfo: SectionInfo,
                          items: PrintOfferItem[],
                          editLast = false) {
        const sectionSel = d3.select(this.editorSelector).select(`.section.${sectionInfo.section}`);
        const updateSel = sectionSel
            .selectAll('foreignObject.item')
            .data(items);
        const enterSel = updateSel.enter()
            .append('foreignObject')
            .attr('class', 'item')
        ;
        enterSel.append('xhtml:div');
        /*const exitSel =*/
        updateSel.exit().remove();

        enterSel.merge(updateSel)
            .each((item: PrintOfferItem, i, g) => {
                item.draw(<SVGForeignObjectElement>g[i]);
            })
        ;
        if (editLast) {
            const nodes = <SVGForeignObjectElement[]>enterSel.nodes();
            d3.select<SVGForeignObjectElement, PrintOfferItem>(nodes[nodes.length - 1]).datum().startEdit(true);
        }

        sectionSel
            .selectAll('foreignObject.bottom-buttons')
            .data([sectionInfo])
            .enter()
            .append('foreignObject')
            .attr('class', 'bottom-buttons')
            .each((d, i, g) => {
                const html =
                    `<div>
                        <a href="#" title="${sectionInfo.btnTitle}">
                          <i class="btn add fas fa-plus"></i>
                        </a>
                     </div>`
                ;
                const height = this.getHtmlHeight(html);
                d3.select(g[i])
                    .attr('width', `${this.colwidth}px`)
                    .attr('height', `${height}px`)
                    .html(html)
                    .on('click', () => this.onBottomBtnClick(sectionInfo))
                    .select('div')
                    .style('height', `${height}px`)
                ;
            })
        ;
    }

    updateLayout() {
        let maxColHeight = 0;
        d3.select(this.editorSelector).select('g.printoffer-items')
            .selectAll('g') // sections
            .each((d, i, g) => {
                let divs = <HTMLDivElement[]>d3.select(g[i])
                    .selectAll('foreignObject.item > div')
                    .nodes()

                let colHeight = 0;
                for (let j = 0; j < divs.length; j++) {
                    const fo = <SVGForeignObjectElement><unknown>divs[j].parentElement;
                    d3.select<SVGForeignObjectElement, PrintOfferItem>(fo)
                        .datum().moveTo(i * (this.colwidth + PrintOptionsEditor.COLS_MARGIN), colHeight + this.headerHeight)
                    ;
                    colHeight += parseFloat(divs[j].style.height) + PrintOptionsEditor.ROW_MARGIN;
                }

                divs = <HTMLDivElement[]>d3.select(g[i]).selectAll('foreignObject.bottom-buttons > div').nodes();
                for (let j = 0; j < divs.length; j++) {
                    const fo = <SVGForeignObjectElement><unknown>divs[j].parentElement;
                    d3.select<SVGForeignObjectElement, PrintOfferItem>(fo)
                        .transition().duration(TR_DURATION)
                        .attr('transform', `translate(${i * (this.colwidth + PrintOptionsEditor.COLS_MARGIN)},${colHeight + this.headerHeight})`);
                }
                colHeight += parseFloat(divs[0].style.height);
                maxColHeight = Math.max(maxColHeight, colHeight);
            })
        ;
        d3.select(this.editorSelector).select('svg')
            .transition().duration(TR_DURATION)
            .attr('height', `${this.headerHeight + maxColHeight}px`)
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

    private static formatViewHtml(item: IPrintOfferItem): string {
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


    private static finishViewHtml(item: IPrintOfferItem): string {
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

    private static frameViewHtml(item: IPrintOfferItem): string {
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

    static checkTextareaLines(ta: HTMLTextAreaElement): boolean {
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

    private onBottomBtnClick(sectionInfo: SectionInfo) {
        const evt = d3.event;
        const target = evt.target;
        if (target.classList.contains('btn')) {
            evt.stopPropagation();
            evt.preventDefault();
            if (target.classList.contains('add')) {
                this.createPrintOfferItem(sectionInfo);
            }
        }


    }

    private createPrintOfferItem(sectionInfo: SectionInfo) {
        let params: FormData = new FormData();
        params.append('section', sectionInfo.section);
        let url = `${this.absUrl}/printingOptions/printoffer/getTemplate`;
        d3.json(
            url,
            {
                body: params,
                method: 'POST'
            }
        ).then((item: IPrintOfferItem) => {
            const data = d3.select(this.editorSelector)
                .select(`.section.${sectionInfo.section}`)
                .selectAll('foreignObject.item')
                .data()
            data.push(new PrintOfferItem(this, sectionInfo, item));
            this.updateSection(sectionInfo, <PrintOfferItem[]>data, true);
            this.updateLayout();
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