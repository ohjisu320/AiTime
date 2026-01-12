/*
 * [나이순 정렬]
 * 나이와 이름이 순서대로 주어짐
 * 나이가 증가하는 순으로,
 * 나이가 같으면 먼저 가입한 사람이 앞에 오는 순서로 정렬
 * 
 * # 풀이
 * 클래스 선언 후 
 * priority queue 로 정렬하기
 * 
 */

import java.io.*;
import java.util.*;

class Member {
	int age;
	String name;
	int order;
	
	public Member(int age, String name, int order) {
		this.age = age;
		this.name = name;
		this.order = order;
	}
}

public class Main {
	
	public static void main(String[] args) throws IOException {
		BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
		BufferedWriter bw = new BufferedWriter(new OutputStreamWriter(System.out));
		StringTokenizer st;
		StringBuilder sb = new StringBuilder();
		
		int n = Integer.parseInt(br.readLine());
		PriorityQueue<Member> members = new PriorityQueue<Member>(
			(a,b) -> {
				if (a.age == b.age) return Integer.compare(a.order, b.order);
				return Integer.compare(a.age, b.age);
			}
		);
		
		for (int i = 0; i < n; i++) {
			st = new StringTokenizer(br.readLine());
			int age = Integer.parseInt(st.nextToken());
			String name = st.nextToken();
			
			members.add(new Member(age, name, i));
		}
		
		while (!members.isEmpty()) {
			Member m = members.poll();
			sb.append(m.age).append(" ").append(m.name).append("\n");
		}
		
		bw.write(sb.toString());
		bw.flush();
		bw.close();
		br.close();
	}
}
