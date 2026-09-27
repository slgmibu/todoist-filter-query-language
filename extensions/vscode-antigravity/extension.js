const vscode = require('vscode');

function formatSingleClause(clause) {
    let line = clause.trim();
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
    const keywords = [
        "today", "tomorrow", "yesterday", "now", "overdue", "recurring",
        "subtask", "uncompletable", "shared", "assigned", "all",
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "mon", "tue", "wed", "thu", "fri", "sat", "sun",
        "january", "february", "march", "april", "may", "june", "july",
        "august", "september", "october", "november", "december",
        "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
        "me", "others", "first day", "last day"
    ];
    for (const kw of keywords) {
        const regex = new RegExp(`\\b${kw}\\b`, 'gi');
        line = line.replace(regex, kw);
    }

    // 5. Normalize operators: unary ! (0 spaces after), binary & and | (1 space around, ignore escaped \&)
    line = line.replace(/(?<!\\)\s*([&|])\s*/g, ' $1 ');
    line = line.replace(/!\s+/g, '!');

    // 6. Normalize parentheses padding
    line = line.replace(/\(\s+/g, '(');
    line = line.replace(/\s+\)/g, ')');
    line = line.replace(/([^\s!(])\(/g, '$1 (');
    line = line.replace(/\)([^\s),])/g, ') $1');

    // Collapse multiple spaces
    line = line.replace(/[ \t]{2,}/g, ' ');

    return line.trim();
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

function formatDocumentText(text) {
    const lines = text.split(/\r?\n/);
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
                const formatted = formatSingleClause(clauses[i]);
                outputLines.push(i < clauses.length - 1 ? `${formatted},` : formatted);
            }
        } else {
            outputLines.push(formatSingleClause(stripped));
        }
    }
    return outputLines.join('\n') + (text.endsWith('\n') ? '\n' : '');
}

function activate(context) {
    const provider = vscode.languages.registerDocumentFormattingEditProvider('tfql', {
        provideDocumentFormattingEdits(document) {
            const fullText = document.getText();
            const formatted = formatDocumentText(fullText);
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
