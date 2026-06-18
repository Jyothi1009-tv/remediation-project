package com.example.demo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication(scanBasePackages = "com.example")
@RestController
public class DemoApplication {

    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }

    /**
     * Simple endpoint to verify the application is up and running.
     */
    @GetMapping("/")
    public String healthCheck() {
        return "OSS Upgrade Demo Application is running successfully!";
    }

    /**
     * Example endpoint that could utilize logic from app-service.
     */
    @GetMapping("/status")
    public String getStatus() {
        return "System Status: Healthy. Ready for dependency vulnerability scanning.";
    }
}
