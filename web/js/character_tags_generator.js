// CharacterTagsGenerator: the sex toggles as one row of chips, and each
// year limit as its toggle and year on one row.
//
// The node declares plain widgets -- BOOLEANs girl, boy and other, and a
// BOOLEAN year_min / year_max with an INT <name>_value -- because that is
// all INPUT_TYPES can express. As in tags_generator_categories.js the
// originals are hidden rather than removed, so widget order, and with it
// serialisation and the prompt the backend receives, is untouched.
import { app } from "../../scripts/app.js";
import { drawToggle, isLowQuality } from "./tags_generator_categories.js";

const NODE = "CharacterTagsGenerator";
const SEXES = ["girl", "boy", "other"];
const YEARS = ["year_min", "year_max"];
const VALUE_SUFFIX = "_value";

function hide(widget) {
    widget.computeSize = () => [0, -4];
    widget.draw = () => {};
    widget.type = "alchemine-hidden";
}

function drawFrame(ctx, node, y, height) {
    const margin = 15;
    ctx.strokeStyle = LiteGraph.WIDGET_OUTLINE_COLOR;
    ctx.fillStyle = LiteGraph.WIDGET_BGCOLOR;
    ctx.beginPath();
    ctx.roundRect(margin, y, node.size[0] - margin * 2, height,
                  isLowQuality() ? [0] : [height * 0.5]);
    ctx.fill();
    if (!isLowQuality()) ctx.stroke();
    return margin;
}

const within = (pos, bounds) =>
    bounds && pos[0] >= bounds[0] && pos[0] <= bounds[0] + bounds[1];

function makeSexRow(widgets) {
    // an extra widget that is only drawn: the toggles stay in node.widgets
    // and serialise themselves, and serialize: false keeps this one out of
    // both widgets_values and the prompt
    const row = {
        type: "custom",
        name: "sex",
        value: null,
        serialize: false,
        options: { serialize: false },
        tooltip: widgets[0].options?.tooltip ?? "",
        computeSize(width) { return [width, LiteGraph.NODE_WIDGET_HEIGHT]; },
    };
    row.draw = function (ctx, node, width, y, height) {
        ctx.save();
        const margin = drawFrame(ctx, node, y, height);
        if (isLowQuality()) { ctx.restore(); return; }
        const midY = y + height * 0.5;
        let x = margin + 12;
        ctx.textBaseline = "middle";
        ctx.textAlign = "left";
        ctx.fillStyle = LiteGraph.WIDGET_SECONDARY_TEXT_COLOR || "#999";
        ctx.fillText("sex", x, midY);
        // chips from the right edge, so the label keeps the left
        const chipW = Math.min(60, (node.size[0] - margin * 2 - 60) / widgets.length);
        let right = node.size[0] - margin - 6;
        this.chips = [];
        for (let i = widgets.length - 1; i >= 0; i--) {
            const left = right - chipW;
            ctx.beginPath();
            ctx.roundRect(left + 2, y + 3, chipW - 4, height - 6, [height * 0.4]);
            ctx.fillStyle = widgets[i].value ? "#89B" : "rgba(255,255,255,0.08)";
            ctx.fill();
            ctx.fillStyle = widgets[i].value ? "#fff" : LiteGraph.WIDGET_TEXT_COLOR;
            ctx.textAlign = "center";
            ctx.fillText(widgets[i].name, left + chipW / 2, midY);
            this.chips[i] = [left, chipW];
            right = left;
        }
        ctx.restore();
    };
    row.mouse = function (event, pos, node) {
        if (event.type !== "pointerdown") return false;
        const i = (this.chips ?? []).findIndex(b => within(pos, b));
        if (i < 0) return false;
        // at least one stays on: the last one on cannot be switched off
        if (widgets[i].value && widgets.filter(w => w.value).length === 1) return true;
        widgets[i].value = !widgets[i].value;
        node.setDirtyCanvas(true, true);
        return true;
    };
    return row;
}

function makeYearRow(toggle, year) {
    const row = {
        type: "custom",
        name: year.name,
        options: year.options,
        tooltip: `${toggle.options?.tooltip ?? ""}\n\n${year.options?.tooltip ?? ""}`.trim(),
        get value() { return year.value; },
        set value(v) { year.value = v; },
        serializeValue() { return year.value; },
        computeSize(width) { return [width, LiteGraph.NODE_WIDGET_HEIGHT]; },
    };
    row.draw = function (ctx, node, width, y, height) {
        ctx.save();
        const margin = drawFrame(ctx, node, y, height);
        let x = margin + 6;
        this.toggleBounds = [x, drawToggle(ctx, x, y, height, toggle.value)];
        x += this.toggleBounds[1] + 5;
        if (isLowQuality()) { ctx.restore(); return; }
        if (!toggle.value) ctx.globalAlpha = app.canvas.editor_alpha * 0.4;
        const midY = y + height * 0.5;
        ctx.textBaseline = "middle";
        ctx.fillStyle = LiteGraph.WIDGET_SECONDARY_TEXT_COLOR || "#999";
        ctx.textAlign = "left";
        ctx.fillText(toggle.name, x, midY);
        const right = node.size[0] - margin - 8;
        ctx.fillStyle = LiteGraph.WIDGET_TEXT_COLOR;
        ctx.textAlign = "right";
        ctx.fillText(String(year.value), right - 12, midY);
        ctx.textAlign = "center";
        ctx.fillText("◀", x + 4 + (right - x) * 0.62, midY);
        ctx.fillText("▶", right - 4, midY);
        this.decBounds = [x + (right - x) * 0.62 - 6, 16];
        this.incBounds = [right - 12, 16];
        ctx.restore();
    };
    row.mouse = function (event, pos, node) {
        if (event.type !== "pointerdown") return false;
        if (within(pos, this.toggleBounds)) {
            toggle.value = !toggle.value;
            node.setDirtyCanvas(true, true);
            return true;
        }
        if (!toggle.value) return true;          // off: the year is inert
        const min = year.options?.min ?? 2005;
        const max = year.options?.max ?? 2025;
        const clamp = v => Math.min(max, Math.max(min, Math.round(v)));
        let delta = 0;
        if (within(pos, this.decBounds)) delta = -1;
        else if (within(pos, this.incBounds)) delta = 1;
        if (delta) {
            year.value = clamp(year.value + delta);
            node.setDirtyCanvas(true, true);
            return true;
        }
        app.canvas.prompt("Value", year.value, (v) => {
            const parsed = Number(v);
            if (!Number.isNaN(parsed)) {
                year.value = clamp(parsed);
                node.setDirtyCanvas(true, true);
            }
        }, event);
        return true;
    };
    return row;
}

app.registerExtension({
    name: "alchemine.generatorPack.CharacterRows",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE) return;
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);
            const byName = name => this.widgets?.find(w => w.name === name);
            const sexes = SEXES.map(byName);
            if (sexes.every(Boolean)) {
                sexes.forEach(hide);
                this.widgets.splice(this.widgets.indexOf(sexes[0]), 0, makeSexRow(sexes));
            }
            for (const name of YEARS) {
                const toggle = byName(name);
                const year = byName(name + VALUE_SUFFIX);
                if (!toggle || !year) continue;
                hide(toggle);
                this.widgets[this.widgets.indexOf(year)] = makeYearRow(toggle, year);
            }
            this.setSize(this.computeSize());
            return result;
        };
    },
});
