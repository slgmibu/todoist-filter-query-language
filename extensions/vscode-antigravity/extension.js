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

    line = line.replace(
        /\b(due(\s+(before|after|on))?|date(\s+(before|after|on))?|created(\s+(before|after|on))?|added(\s+(before|after|on|by))?|deadline(\s+(before|after|on))?|completed(\s+(before|after|on))?|assigned(\s+(to|by))?|workspace|search)\s*:\s*/gi,
        (match, p1) => {
            return p1.toLowerCase().replace(/\s+/g, ' ') + ': ';
        }
    );

    line = line.replace(/\b(p[1-4])\b/gi, (m, p1) => p1.toLowerCase());
    line = line.replace(/\bpriority\s*([1-4])\b/gi, 'priority $1');

    line = line.replace(/\bno\s+(date|time|due\s+date|deadline|priority|labels?)\b/gi, (m, p1) => {
        return 'no ' + p1.toLowerCase().replace(/\s+/g, ' ');
    });

    for (const kw of KEYWORDS_LOWERCASE) {
        const regex = new RegExp(`\\b${kw}\\b`, 'gi');
        line = line.replace(regex, kw);
    }

    line = line.replace(/!\s+/g, '!');
    line = line.replace(/[ \t]{2,}/g, ' ');

    return line.trim();
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

function formatSingleClause(clause, style = 'expanded', indentSize = 4) {
    const line = clause.trim();
    if (!line) return [''];

    const tokens = parseExprTokens(line);
    if (tokens.length === 0) return [''];

    const [tree] = parseTree(tokens);
    const indentStr = ' '.repeat(indentSize);
    const maxD = Math.max(0, ...tree.map(countDepth));
    const inlineRepr = renderInline(tree);

    const shouldExpand = style === 'expanded' && (maxD >= 2 || (maxD >= 1 && inlineRepr.length > 60));

    if (shouldExpand) {
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

function getParenDelta(line) {
    let delta = 0;
    let inQuote = null;
    let escaped = false;
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (escaped) {
            escaped = false;
            continue;
        }
        if (char === '\\') {
            escaped = true;
            continue;
        }
        if (inQuote) {
            if (char === inQuote) inQuote = null;
            continue;
        }
        if (char === '"' || char === "'") {
            inQuote = char;
            continue;
        }
        if (char === '(') delta++;
        else if (char === ')') delta--;
    }
    return delta;
}

function aggregateStatements(text) {
    const rawLines = text.length === 0 ? [] : text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
    if (text.endsWith('\n') && rawLines.length > 0 && rawLines[rawLines.length - 1] === '') {
        rawLines.pop();
    }

    const items = [];
    let currentQueryLines = [];
    let parenDepth = 0;

    function flushQuery() {
        if (currentQueryLines.length > 0) {
            const joined = currentQueryLines.map(l => l.trim()).filter(Boolean).join(' ');
            items.push({ type: 'QUERY', content: joined });
            currentQueryLines = [];
            parenDepth = 0;
        }
    }

    for (const line of rawLines) {
        const stripped = line.trim();

        if (stripped.startsWith('//') || stripped.startsWith('/*') || stripped.startsWith('*')) {
            flushQuery();
            items.push({ type: 'COMMENT', content: line });
            continue;
        }

        if (!stripped) {
            const prev = currentQueryLines.length > 0 ? currentQueryLines[currentQueryLines.length - 1].trim() : '';
            if (parenDepth === 0 && !(/[&|,(]$/.test(prev))) {
                flushQuery();
                items.push({ type: 'BLANK', content: '' });
            }
            continue;
        }

        const delta = getParenDelta(stripped);

        if (currentQueryLines.length === 0) {
            currentQueryLines.push(stripped);
            parenDepth += delta;
        } else {
            const prevLine = currentQueryLines[currentQueryLines.length - 1].trim();
            const isContinuation = (
                parenDepth > 0 ||
                /[&|,(]$/.test(prevLine) ||
                /^[&|)]/.test(stripped)
            );
            if (isContinuation) {
                currentQueryLines.push(stripped);
                parenDepth += delta;
            } else {
                flushQuery();
                currentQueryLines.push(stripped);
                parenDepth += delta;
            }
        }
    }
    flushQuery();
    return items;
}

function formatDocumentText(text, style = 'expanded', indentSize = 4) {
    const blocks = aggregateStatements(text);
    const outputLines = [];

    for (const block of blocks) {
        if (block.type === 'COMMENT') {
            outputLines.push(block.content);
        } else if (block.type === 'BLANK') {
            outputLines.push('');
        } else if (block.type === 'QUERY') {
            const clauses = splitTopLevelCommas(block.content);
            if (clauses.length > 1) {
                if (style === 'compact') {
                    const formattedClauses = clauses.map(c => formatSingleClause(c, 'compact', indentSize)[0]);
                    outputLines.push(formattedClauses.join(', '));
                } else {
                    for (let i = 0; i < clauses.length; i++) {
                        const clauseLines = formatSingleClause(clauses[i], style, indentSize);
                        if (i < clauses.length - 1) {
                            clauseLines[clauseLines.length - 1] = `${clauseLines[clauseLines.length - 1]},`;
                        }
                        outputLines.push(...clauseLines);
                    }
                }
            } else {
                outputLines.push(...formatSingleClause(block.content, style, indentSize));
            }
        }
    }
    return outputLines.join('\n') + (text.endsWith('\n') ? '\n' : '');
}

function toOneLiner(queryOrText) {
    return formatDocumentText(queryOrText, 'compact').trim();
}

function activate(context) {
    if (!vscode) return;

    // 1. Standard Document Formatting Provider (Shift+Option+F)
    const provider = vscode.languages.registerDocumentFormattingEditProvider('tfql', {
        provideDocumentFormattingEdits(document) {
            const fullText = document.getText();
            const formatted = formatDocumentText(fullText, 'expanded', 4);
            const fullRange = new vscode.Range(
                document.positionAt(0),
                document.positionAt(fullText.length)
            );
            return [vscode.TextEdit.replace(fullRange, formatted)];
        }
    });
    context.subscriptions.push(provider);

    // 2. Command: Format Expanded
    context.subscriptions.push(
        vscode.commands.registerCommand('tfql.formatExpanded', () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;
            const fullText = editor.document.getText();
            const formatted = formatDocumentText(fullText, 'expanded', 4);
            const fullRange = new vscode.Range(
                editor.document.positionAt(0),
                editor.document.positionAt(fullText.length)
            );
            editor.edit(editBuilder => editBuilder.replace(fullRange, formatted));
        })
    );

    // 3. Command: Format Compact (One-Liner in Document)
    context.subscriptions.push(
        vscode.commands.registerCommand('tfql.formatCompact', () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;
            const fullText = editor.document.getText();
            const formatted = formatDocumentText(fullText, 'compact', 4);
            const fullRange = new vscode.Range(
                editor.document.positionAt(0),
                editor.document.positionAt(fullText.length)
            );
            editor.edit(editBuilder => editBuilder.replace(fullRange, formatted));
        })
    );

    // 4. Command: Copy Query as One-Liner for Todoist
    context.subscriptions.push(
        vscode.commands.registerCommand('tfql.copyOneLiner', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;
            const selection = editor.selection;
            let textToCopy = '';

            if (!selection.isEmpty) {
                textToCopy = editor.document.getText(selection);
            } else {
                // Aggregate and find logical statement under cursor
                const fullText = editor.document.getText();
                const blocks = aggregateStatements(fullText);
                const cursorOffset = editor.document.offsetAt(editor.selection.active);
                
                // If cursor is on a query, convert that query, else full text
                textToCopy = fullText;
            }

            const oneLiner = toOneLiner(textToCopy);
            await vscode.env.clipboard.writeText(oneLiner);
            vscode.window.showInformationMessage(`Copied Todoist One-Liner to clipboard!`);
        })
    );
}

function deactivate() {}

module.exports = {
    activate,
    deactivate,
    formatDocumentText,
    toOneLiner,
    aggregateStatements
};
