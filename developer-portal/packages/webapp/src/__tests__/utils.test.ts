/**
 * slugify 函数单元测试
 *
 * slugify 的作用：把用户输入的组织名转成合法的 URL slug。
 * 例如：用户输入 "My Company!" → slug 变成 "my-company"
 */
import { test, expect, describe } from "bun:test";
import { slugify } from "../lib/utils";

describe("slugify — 把名字转成合法 URL slug", () => {

  test("大写字母全部转成小写", () => {
    // "Hello World" → "hello-world"
    expect(slugify("Hello World")).toBe("hello-world");
  });

  test("空格和特殊符号替换成连字符", () => {
    // "My Org Name!" 里的空格和感叹号都换成 -，末尾的 - 去掉
    expect(slugify("My Org Name!")).toBe("my-org-name");
  });

  test("连续的分隔符只保留一个连字符", () => {
    // "foo  --  bar" 中间有多个空格和横线，合并成一个 -
    expect(slugify("foo  --  bar")).toBe("foo-bar");
  });

  test("去掉头尾的空格和连字符", () => {
    // "  hello  " 前后的空格不保留
    expect(slugify("  hello  ")).toBe("hello");
  });

  test("本来就合法的 slug 保持不变", () => {
    // "my-org-123" 已经是合法 slug，不做任何修改
    expect(slugify("my-org-123")).toBe("my-org-123");
  });

  test("全是特殊字符时返回空字符串", () => {
    // "!!!" 没有任何字母或数字，结果是空串
    expect(slugify("!!!")).toBe("");
  });

});
