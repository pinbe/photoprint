import * as d3 from "d3";

type Sel = d3.Selection<HTMLElement, any, HTMLElement, any>;

class PrintOptionsEditor {
    constructor() {
        const cells = d3.selectAll('#print_options_editor > tr > td');
        console.log(cells.size());
    }
}

function main() {
    new PrintOptionsEditor();
}

window.addEventListener('load', ()=>main());