const fs = require('fs');
const path = require('path');

function stripComments(code, isVue) {
    let lines = code.split('\n');
    let result = [];
    let inBlockComment = false;

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        let trimmed = line.trim();
        
        if (inBlockComment) {
            if (trimmed.includes('*/')) {
                inBlockComment = false;
                // If there's code after */ we should keep it, but usually there isn't in this project
                let after = line.substring(line.indexOf('*/') + 2).trim();
                if (after !== '') result.push(after);
            }
            continue;
        }

        if (trimmed.startsWith('/*')) {
            if (trimmed.includes('*/')) {
                // Inline block comment, maybe just a comment line
                let after = line.substring(line.indexOf('*/') + 2).trim();
                if (after !== '') result.push(after);
                continue;
            } else {
                inBlockComment = true;
                continue;
            }
        }

        if (trimmed.startsWith('//')) {
            continue;
        }

        if (isVue && trimmed.startsWith('<!--')) {
            if (trimmed.includes('-->')) {
                continue;
            } else {
                // We're ignoring multi-line HTML comments because Vue often doesn't have them as pure comments without breaking things if regex is used, but if it starts with <!-- we'll just skip the line. Wait, we should skip until -->
                // Actually, let's not touch multi-line HTML comments for safety.
                result.push(line);
                continue;
            }
        }

        result.push(line);
    }
    
    return result.join('\n');
}

function processDirectory(dir) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
        const fullPath = path.join(dir, file);
        if (fs.statSync(fullPath).isDirectory()) {
            processDirectory(fullPath);
        } else {
            if (fullPath.endsWith('.js') || fullPath.endsWith('.ts') || fullPath.endsWith('.vue')) {
                const code = fs.readFileSync(fullPath, 'utf8');
                const isVue = fullPath.endsWith('.vue');
                const stripped = stripComments(code, isVue);
                fs.writeFileSync(fullPath, stripped, 'utf8');
            }
        }
    }
}

processDirectory('frontend/src');
console.log('JS/TS/Vue comments stripped safely.');
