let vscode;
try {
    vscode = require('vscode');
} catch (_) {}

const KEYWORDS_LOWERCASE = new Set([
    "today", "tomorrow", "yesterday", "now", "overdue", "recurring",
    "subtask", "uncompletable", "shared", "assigned", "all",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "mon", "tue", "wed", "thu", "fri", "sat", "sun",
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
    "me", "others", "first day", "last day"
]);

function normalizeAtom(atom) {
    let line = atom.trim();
    if (!line) return "";

    // 1. Normalize predicates (e.g. "due  :   today" -> "due: today")
    line = line.replace(
        /\b(due(\s+(before|after|on))?|date(\s+(before|after|on))?|created(\s+(before|after|on))?|added(\s+(before|after|on|by))?|deadline(\s+(before|after|on))?|completed(\s+(before|after|on))?|assigned(\s+(to|by))?|workspace|search)\s*:\s*/gi,
        (match, p1) => {
            return p1.toLowerCase().replace(/\s+/g, ' ') + ': ';
        }
    );

    // 2. Normalize priority tokens (e.g. "P1" -> "p1", "priority  1" -> "priority 1")
    line = line.replace(/\b(p[1-4])\b/gi, (m, p1) => p1.toLowerCase());
    line = line.replace(/\bpriority\s*([1-4])\b/gi, 'priority $1');

    // 3. Normalize negative flags (e.g. "no   date" -> "no date")
    line = line.replace(/\bno\s+(date|time|due\s+date|deadline|priority|labels?)\b/gi, (m, p1) => {
        return 'no ' + p1.toLowerCase().replace(/\s+/g, ' ');
    });

    // 4. Normalize common temporal keywords
    for (const kw of KEYWORDS_LOWERCASE) {
        const regex = new RegExp(`\\b${kw}\\b`, 'gi');
        line = line.replace(regex, kw);
    }

    // 5. Unary NOT: remove spaces after !
    line = line.replace(/!\s+/g, '!');

    // 6. Collapse incidental multiple spaces
    line = line.replace(/[ \t]{2,}/g, ' ');

    return line.strip ? line.strip() : line.trim();
}

function parseExprTokens(s) {
    const tokens = [];
    let i = 0;
    const n = s.length;

    while (i < n) {
        if (/\s/.test(s[i])) {
            i++;
            continue;
        }
        if (s[i] === '&' || s[i] === '|') {
            tokens.push({ type: 'OP', val: s[i] });
            i++;
            continue;
        }
        if (s[i] === '!') {
            let j = i + 1;
            while (j < n && /\s/.test(s[j])) {
                j++;
            }
            if (j < n && s[j] === '(') {
                tokens.push({ type: 'NOT_GROUP', val: '!' });
                i = j;
                continue;
            }
        }
        if (s[i] === '(') {
            tokens.push({ type: 'LPAREN', val: '(' });
            i++;
            continue;
        }
        if (s[i] === ')') {
            tokens.push({ type: 'RPAREN', val: ')' });
            i++;
            continue;
        }

        // Atom phrase
        const start = i;
        let inQuote = null;
        while (i < n) {
            if (inQuote) {
                if (s[i] === '\\' && i + 1 < n) {
                    i += 2;
                    continue;
                }
                if (s[i] === inQuote) {
                    inQuote = null;
                }
                i++;
                continue;
            }
            if (s[i] === '"' || s[i] === "'") {
                inQuote = s[i];
                i++;
                continue;
            }
            if (s[i] === '\\' && i + 1 < n) {
                i += 2;
                continue;
            }
            if (s[i] === '&' || s[i] === '|' || s[i] === '(' || s[i] === ')') {
                break;
            }
            i++;
        }
        tokens.push({ type: 'ATOM', val: normalizeAtom(s.slice(start, i)) });
    }
    return tokens;
}

function parseTree(tokens, idx = 0) {
    const elements = [];
    let prefix = '';

    while (idx < tokens.length) {
        const token = tokens[idx];
        if (token.type === 'LPAREN') {
            const [sub, nextIdx] = parseTree(tokens, idx + 1);
            elements.push({ type: 'GROUP', prefix: prefix + '(', sub });
            prefix = '';
            idx = nextIdx;
        } else if (token.type === 'NOT_GROUP') {
            prefix = '!';
            idx++;
        } else if (token.type === 'RPAREN') {
            return [elements, idx + 1];
        } else {
            elements.push(token);
            idx++;
        }
    }
    return [elements, idx];
}

function countDepth(item) {
    if (item.type === 'GROUP') {
        const subDepths = item.sub.map(countDepth);
        return 1 + (subDepths.length > 0 ? Math.max(...subDepths) : 0);
    }
    return 0;
}

function renderInline(elements) {
    const res = [];
    for (const el of elements) {
        if (el.type === 'GROUP') {
            res.push(`${el.prefix}${renderInline(el.sub)})`);
        } else if (el.type === 'OP') {
            res.push(` ${el.val} `);
        } else {
            res.push(el.val);
        }
    }
    return res.join('').trim();
}

function prettyPrintTree(elements, indentLevel = 0, indentStr = '    ') {
    const lines = [];
    let currentOp = '';
    let i = 0;

    while (i < elements.length) {
        const el = elements[i];
        if (el.type === 'OP') {
            currentOp = el.val;
            i++;
            continue;
        }

        const prefix = currentOp ? `${currentOp} ` : '';
        currentOp = '';

        if (el.type === 'GROUP') {
            const inlineStr = renderInline(el.sub);
            const depth = countDepth(el);

            const isSimpleLeaf = depth <= 1 && inlineStr.length < 45 &&
                !el.sub.some(x => x.type === 'OP' && x.val === '|' && countDepth(x) > 0);

            if (isSimpleLeaf) {
                lines.push(`${indentStr.repeat(indentLevel)}${prefix}${el.prefix}${inlineStr})`);
            } else {
                lines.push(`${indentStr.repeat(indentLevel)}${prefix}${el.prefix}`);
                const subLines = prettyPrintTree(el.sub, indentLevel + 1, indentStr);
                lines.push(...subLines);
                lines.push(`${indentStr.repeat(indentLevel)})`);
            }
        } else {
            lines.push(`${indentStr.repeat(indentLevel)}${prefix}${el.val}`);
        }
        i++;
    }
    return lines;
}

function formatSingleClause(clause, indentSize = 4) {
    const line = clause.trim();
    if (!line) return [''];

    const tokens = parseExprTokens(line);
    if (tokens.length === 0) return [''];

    const [tree] = parseTree(tokens);
    const indentStr = ' '.repeat(indentSize);
    const maxD = Math.max(0, ...tree.map(countDepth));
    const inlineRepr = renderInline(tree);

    if (maxD >= 2 || (maxD >= 1 && inlineRepr.length > 60)) {
        return prettyPrintTree(tree, 0, indentStr);
    } else {
        return [inlineRepr];
    }
}

function splitTopLevelCommas(line) {
    const clauses = [];
    let current = [];
    let parenDepth = 0;
    let inQuote = null;
    let escaped = false;

    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (escaped) {
            current.push(char);
            escaped = false;
            continue;
        }
        if (char === '\\') {
            current.push(char);
            escaped = true;
            continue;
        }
        if (inQuote) {
            current.push(char);
            if (char === inQuote) inQuote = null;
            continue;
        }
        if (char === '"' || char === "'") {
            inQuote = char;
            current.push(char);
            continue;
        }
        if (char === '(') {
            parenDepth++;
            current.push(char);
            continue;
        } else if (char === ')') {
            if (parenDepth > 0) parenDepth--;
            current.push(char);
            continue;
        }
        if (char === ',' && parenDepth === 0) {
            clauses.push(current.join('').trim());
            current = [];
        } else {
            current.push(char);
        }
    }
    if (current.length > 0) {
        clauses.push(current.join('').trim());
    }
    return clauses.filter(Boolean);
}

function formatDocumentText(text, indentSize = 4) {
    // Mirror Python splitlines() behavior
    const lines = text.length === 0 ? [] : text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
    if (text.endsWith('\n') && lines.length > 0 && lines[lines.length - 1] === '') {
        lines.pop();
    }

    const outputLines = [];

    for (const line of lines) {
        const stripped = line.trim();
        if (!stripped || stripped.startsWith('//') || stripped.startsWith('/*') || stripped.startsWith('*')) {
            outputLines.push(stripped);
            continue;
        }
        const clauses = splitTopLevelCommas(stripped);
        if (clauses.length > 1) {
            for (let i = 0; i < clauses.length; i++) {
                const clauseLines = formatSingleClause(clauses[i], indentSize);
                if (i < clauses.length - 1) {
                    clauseLines[clauseLines.length - 1] = `${clauseLines[clauseLines.length - 1]},`;
                }
                outputLines.push(...clauseLines);
            }
        } else {
            outputLines.push(...formatSingleClause(stripped, indentSize));
        }
    }
    return outputLines.join('\n') + (text.endsWith('\n') ? '\n' : '');
}

function activate(context) {
    if (!vscode) return;
    const provider = vscode.languages.registerDocumentFormattingEditProvider('tfql', {
        provideDocumentFormattingEdits(document) {
            const fullText = document.getText();
            const formatted = formatDocumentText(fullText, 4);
            const fullRange = new vscode.Range(
                document.positionAt(0),
                document.positionAt(fullText.length)
            );
            return [vscode.TextEdit.replace(fullRange, formatted)];
        }
    });
    context.subscriptions.push(provider);
}

function deactivate() {}

module.exports = {
    activate,
    deactivate,
    formatDocumentText
};
