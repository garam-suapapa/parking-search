#!/usr/bin/env node
/**
 * Translates all markdown files in ~/.claude/ (rules, skills, agents, commands, hooks)
 * to Korean using Anthropic Claude API.
 *
 * Usage: ANTHROPIC_API_KEY=sk-ant-xxx node translate-to-korean.js
 */

const fs = require('fs');
const path = require('path');
const Anthropic = require('@anthropic-ai/sdk');

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const CLAUDE_HOME = path.join(process.env.HOME || process.env.USERPROFILE, '.claude');
const TARGET_DIRS = ['rules', 'skills', 'agents', 'commands', 'hooks'];
const CONCURRENCY = 5; // parallel requests at a time

function getAllMarkdownFiles(baseDir) {
  const results = [];
  function walk(dir) {
    if (!fs.existsSync(dir)) return;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name.endsWith('.md')) results.push(full);
    }
  }
  walk(baseDir);
  return results;
}

async function translateFile(filePath) {
  const original = fs.readFileSync(filePath, 'utf-8');

  // Skip already-translated files (heuristic: >30% Korean chars)
  const koreanChars = (original.match(/[\uAC00-\uD7AF]/g) || []).length;
  const totalChars = original.replace(/\s/g, '').length;
  if (totalChars > 0 && koreanChars / totalChars > 0.3) {
    console.log(`SKIP (already Korean): ${filePath}`);
    return;
  }

  try {
    const response = await client.messages.create({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 4096,
      messages: [{
        role: 'user',
        content: `다음 마크다운 파일을 한국어로 번역해주세요. 규칙:
1. 마크다운 문법(#, **, \`\`\`, - 등)은 그대로 유지
2. 코드 블록 안의 코드는 번역하지 말고 그대로 유지
3. YAML frontmatter(--- 사이)의 키(name, description, tools, model 등)는 그대로, 값 중 설명 텍스트만 번역
4. 파일 경로, 변수명, 함수명, 명령어는 번역하지 말 것
5. 번역 결과만 출력 (설명 없이)

---
${original}`
      }]
    });

    const translated = response.content[0].text;
    fs.writeFileSync(filePath, translated, 'utf-8');
    console.log(`OK: ${filePath}`);
  } catch (err) {
    console.error(`ERROR: ${filePath} — ${err.message}`);
  }
}

async function runWithConcurrency(tasks, limit) {
  let index = 0;
  const workers = Array(limit).fill(null).map(async () => {
    while (index < tasks.length) {
      const task = tasks[index++];
      await task();
    }
  });
  await Promise.all(workers);
}

async function main() {
  if (!process.env.ANTHROPIC_API_KEY) {
    console.error('ERROR: ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.');
    console.error('사용법: ANTHROPIC_API_KEY=sk-ant-xxx node translate-to-korean.js');
    process.exit(1);
  }

  const allFiles = [];
  for (const dir of TARGET_DIRS) {
    const fullDir = path.join(CLAUDE_HOME, dir);
    allFiles.push(...getAllMarkdownFiles(fullDir));
  }

  console.log(`총 ${allFiles.length}개 파일 번역 시작...`);

  const tasks = allFiles.map(f => () => translateFile(f));
  await runWithConcurrency(tasks, CONCURRENCY);

  console.log('\n번역 완료!');
}

main().catch(console.error);
